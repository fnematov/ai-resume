import html
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decrypt_secret
from app.services.gdpr import compute_delete_after, erase_candidate
from app.models import (
    ActivityActor,
    ActivityType,
    Application,
    ApplicationSource,
    ApplicationStage,
    ApplicationStatus,
    Candidate,
    Message,
    MessageDirection,
    MessageStatus,
    Organization,
    Submission,
    SubmissionStatus,
    Vacancy,
    VacancyStatus,
)
from app.services.activities import log_activity
from app.services.extraction import ALLOWED_EXTENSIONS, guess_mime
from app.services.storage import save_resume
from app.services.telegram.client import TelegramClient
from app.services.telegram.i18n import (
    CHOOSE_LANGUAGE,
    DEFAULT_LANG,
    SUPPORTED_LANGS,
    language_keyboard,
    t,
)
from app.services.telegram.state import (
    clear_awaiting_cover_letter,
    clear_awaiting_submission,
    clear_pending_start,
    clear_selected_vacancy,
    get_awaiting_cover_letter,
    get_awaiting_submission,
    get_language,
    get_pending_start,
    get_selected_vacancy,
    set_awaiting_cover_letter,
    set_language,
    set_pending_start,
    set_selected_vacancy,
)

async def _resolve_lang(db: AsyncSession, org_id: int, chat_id: int, tg_user: dict) -> str:
    """Current candidate language: Redis first, then the persisted candidate, else default."""
    lang = await get_language(org_id, chat_id)
    if lang in SUPPORTED_LANGS:
        return lang
    cand = (
        await db.execute(
            select(Candidate).where(
                Candidate.org_id == org_id,
                Candidate.telegram_user_id == tg_user.get("id"),
            )
        )
    ).scalar_one_or_none()
    if cand and cand.language in SUPPORTED_LANGS:
        return cand.language
    return DEFAULT_LANG


async def _open_vacancies(db: AsyncSession, org_id: int) -> list[Vacancy]:
    stmt = (
        select(Vacancy)
        .where(Vacancy.org_id == org_id, Vacancy.status == VacancyStatus.open)
        .order_by(Vacancy.created_at.desc())
    )
    return list((await db.execute(stmt)).scalars().all())


async def _vacancy_by_param(db: AsyncSession, org_id: int, param: str) -> Vacancy | None:
    stmt = select(Vacancy).where(
        Vacancy.org_id == org_id,
        Vacancy.deep_link_param == param,
        Vacancy.status == VacancyStatus.open,
    )
    return (await db.execute(stmt)).scalar_one_or_none()


def _vacancy_keyboard(vacancies: list[Vacancy]) -> dict:
    return {
        "inline_keyboard": [
            [{"text": v.title, "callback_data": v.deep_link_param or f"job_{v.id}"}]
            for v in vacancies
        ]
    }


async def _prompt_for_vacancy(
    client: TelegramClient, chat_id: int, vacancy: Vacancy, org: Organization, lang: str
) -> None:
    """Send the full vacancy details + company profile, then ask for the resume."""
    e = html.escape
    lines = [f"<b>{e(vacancy.title)}</b>", f"🏢 {e(org.name)}"]
    meta = []
    if vacancy.location:
        meta.append(f"📍 {e(vacancy.location)}")
    if vacancy.employment_type:
        meta.append(e(vacancy.employment_type))
    if meta:
        lines.append(" · ".join(meta))
    if (vacancy.description or "").strip():
        lines += ["", e(vacancy.description.strip()[:1500])]
    if (vacancy.requirements or "").strip():
        lines += ["", f"<b>{t(lang, 'job_requirements')}</b>", e(vacancy.requirements.strip()[:1200])]
    if (org.about or "").strip():
        lines += ["", f"<b>{t(lang, 'about_company', company=e(org.name))}</b>", e(org.about.strip()[:1000])]
    if org.website:
        lines.append(f"🔗 {e(org.website)}")
    lines += ["", t(lang, "welcome")]
    await client.send_message(chat_id, "\n".join(lines))


async def _start_flow(
    client: TelegramClient, db: AsyncSession, org: Organization, chat_id: int, lang: str, param: str
) -> None:
    """After language is chosen: open the deep-linked vacancy or list open vacancies."""
    if param:
        vacancy = await _vacancy_by_param(db, org.id, param)
        if vacancy:
            await set_selected_vacancy(org.id, chat_id, vacancy.id)
            await _prompt_for_vacancy(client, chat_id, vacancy, org, lang)
            return
        await client.send_message(chat_id, t(lang, "position_closed"))
    vacancies = await _open_vacancies(db, org.id)
    if not vacancies:
        await client.send_message(chat_id, t(lang, "no_open_positions"))
    else:
        await client.send_message(
            chat_id, t(lang, "choose_position"), reply_markup=_vacancy_keyboard(vacancies)
        )


async def _upsert_candidate(
    db: AsyncSession, org_id: int, tg_user: dict, lang: str | None = None
) -> Candidate:
    tg_id = tg_user.get("id")
    cand = (
        await db.execute(
            select(Candidate).where(
                Candidate.org_id == org_id, Candidate.telegram_user_id == tg_id
            )
        )
    ).scalar_one_or_none()
    full_name = " ".join(
        x for x in [tg_user.get("first_name"), tg_user.get("last_name")] if x
    ).strip() or None
    if cand is None:
        cand = Candidate(
            org_id=org_id,
            telegram_user_id=tg_id,
            telegram_username=tg_user.get("username"),
            full_name=full_name,
            language=lang,
        )
        db.add(cand)
        await db.flush()
    else:
        cand.telegram_username = tg_user.get("username") or cand.telegram_username
        cand.full_name = full_name or cand.full_name
        if lang:
            cand.language = lang
    return cand


async def handle_update(
    update: dict, org: Organization, db: AsyncSession, enqueue_score, enqueue_submission
) -> None:
    """Process a single Telegram update for a given org.

    `enqueue_score(app_id)` schedules resume scoring; `enqueue_submission(sub_id)` schedules
    test-task grading.
    """
    token = decrypt_secret(org.telegram_bot_token_enc)  # type: ignore[arg-type]
    client = TelegramClient(token)

    # --- Callback (inline keyboards) ---
    if "callback_query" in update:
        cq = update["callback_query"]
        chat_id = cq["message"]["chat"]["id"]
        cq_user = cq.get("from", {})
        data = cq.get("data", "")
        await client.answer_callback_query(cq["id"])

        # Language selection => store it, then run the deferred /start flow.
        if data.startswith("lang_"):
            lang = data.split("_", 1)[1]
            if lang not in SUPPORTED_LANGS:
                lang = DEFAULT_LANG
            await set_language(org.id, chat_id, lang)
            cand = (
                await db.execute(
                    select(Candidate).where(
                        Candidate.org_id == org.id,
                        Candidate.telegram_user_id == cq_user.get("id"),
                    )
                )
            ).scalar_one_or_none()
            if cand:
                cand.language = lang
                await db.commit()
            param = await get_pending_start(org.id, chat_id) or ""
            await clear_pending_start(org.id, chat_id)
            await _start_flow(client, db, org, chat_id, lang, param)
            return

        lang = await _resolve_lang(db, org.id, chat_id, cq_user)

        # Cover-letter decision after a resume upload.
        if data.startswith("cover_skip_"):
            try:
                app_id = int(data.rsplit("_", 1)[1])
            except (ValueError, IndexError):
                return
            await clear_awaiting_cover_letter(org.id, chat_id)
            enqueue_score(app_id)
            await client.send_message(chat_id, t(lang, "application_reviewing"))
            return
        if data.startswith("cover_add_"):
            try:
                app_id = int(data.rsplit("_", 1)[1])
            except (ValueError, IndexError):
                return
            await set_awaiting_cover_letter(org.id, chat_id, app_id)
            await client.send_message(chat_id, t(lang, "cover_prompt"))
            return

        vacancy = await _vacancy_by_param(db, org.id, data)
        if vacancy:
            await set_selected_vacancy(org.id, chat_id, vacancy.id)
            await _prompt_for_vacancy(client, chat_id, vacancy, org, lang)
        else:
            await client.send_message(chat_id, t(lang, "position_closed"))
        return

    message = update.get("message")
    if not message:
        return
    chat_id = message["chat"]["id"]
    tg_user = message.get("from", {})
    text = message.get("text", "") or ""
    lang = await _resolve_lang(db, org.id, chat_id, tg_user)

    # --- /forget : GDPR right to erasure ---
    if text.startswith("/forget"):
        candidate = (
            await db.execute(
                select(Candidate).where(
                    Candidate.org_id == org.id,
                    Candidate.telegram_user_id == tg_user.get("id"),
                )
            )
        ).scalar_one_or_none()
        if candidate:
            await erase_candidate(db, candidate)
            await db.commit()
            await client.send_message(chat_id, t(lang, "forget_done"))
        else:
            await client.send_message(chat_id, t(lang, "forget_none"))
        return

    # --- /start [payload] : ask for language first, then continue ---
    if text.startswith("/start"):
        parts = text.split(maxsplit=1)
        payload = parts[1].strip() if len(parts) > 1 else ""
        await set_pending_start(org.id, chat_id, payload)
        await client.send_message(chat_id, CHOOSE_LANGUAGE, reply_markup=language_keyboard())
        return

    # --- Resume upload (document or photo) ---
    file_id: str | None = None
    filename: str | None = None
    mime: str | None = None
    if "document" in message:
        doc = message["document"]
        file_id = doc["file_id"]
        filename = doc.get("file_name")
        mime = doc.get("mime_type")
    elif "photo" in message:
        # photos come in sizes; take the largest
        file_id = message["photo"][-1]["file_id"]
        filename = "resume.jpg"
        mime = "image/jpeg"

    # --- Cover letter capture (candidate chose to add one after applying) ---
    cl_app_id = await get_awaiting_cover_letter(org.id, chat_id)
    if cl_app_id is not None:
        if not file_id and not text:
            await client.send_message(chat_id, t(lang, "cover_send_textfile"))
            return
        app_row = await db.get(Application, cl_app_id)
        if app_row is not None:
            if file_id:
                tg_file = await client.get_file(file_id)
                data = await client.download_file(tg_file["file_path"])
                key = save_resume(org.id, data, filename)
                app_row.cover_letter_file_path = key
                app_row.cover_letter_filename = filename
                app_row.cover_letter_mime = guess_mime(filename, mime)
            else:
                app_row.cover_letter_text = text[:20000]
            await db.commit()
            enqueue_score(cl_app_id)
        await clear_awaiting_cover_letter(org.id, chat_id)
        await client.send_message(chat_id, t(lang, "cover_added"))
        return

    if file_id:
        # --- Test-task submission (candidate is in the test_task stage) ---
        sub_app_id = await get_awaiting_submission(org.id, chat_id)
        if sub_app_id is not None:
            tg_file = await client.get_file(file_id)
            data = await client.download_file(tg_file["file_path"])
            key = save_resume(org.id, data, filename)
            app_row = await db.get(Application, sub_app_id)
            sub = Submission(
                org_id=org.id,
                application_id=sub_app_id,
                file_path=key,
                original_filename=filename,
                file_mime=guess_mime(filename, mime),
                status=SubmissionStatus.pending,
            )
            db.add(sub)
            await db.flush()
            if app_row is not None:
                await log_activity(
                    db,
                    application=app_row,
                    type=ActivityType.test_submitted,
                    actor=ActivityActor.candidate,
                    summary=f"Submitted test task ({filename or 'file'})",
                )
            await db.commit()
            enqueue_submission(sub.id)
            await clear_awaiting_submission(org.id, chat_id)
            await client.send_message(chat_id, t(lang, "test_received"))
            return

        vacancy_id = await get_selected_vacancy(org.id, chat_id)
        if vacancy_id is None:
            vacancies = await _open_vacancies(db, org.id)
            if len(vacancies) == 1:
                vacancy_id = vacancies[0].id
            else:
                await client.send_message(
                    chat_id,
                    t(lang, "choose_position_first"),
                    reply_markup=_vacancy_keyboard(vacancies) if vacancies else None,
                )
                return

        # Validate extension
        ext = f".{filename.rsplit('.', 1)[-1].lower()}" if filename and "." in filename else ""
        if ext and ext not in ALLOWED_EXTENSIONS:
            await client.send_message(chat_id, t(lang, "unsupported_file"))
            return

        tg_file = await client.get_file(file_id)
        data = await client.download_file(tg_file["file_path"])
        if len(data) > settings.max_upload_mb * 1024 * 1024:
            await client.send_message(chat_id, t(lang, "file_too_large"))
            return

        candidate = await _upsert_candidate(db, org.id, tg_user, lang)

        # One application per candidate per vacancy — block duplicates.
        already = (
            await db.execute(
                select(Application).where(
                    Application.org_id == org.id,
                    Application.candidate_id == candidate.id,
                    Application.vacancy_id == vacancy_id,
                ).limit(1)
            )
        ).scalar_one_or_none()
        if already is not None:
            await db.commit()  # persist any candidate upsert
            await clear_selected_vacancy(org.id, chat_id)
            await client.send_message(chat_id, t(lang, "already_applied"))
            return

        # Consent + retention (GDPR). Submitting a resume records consent to processing.
        if candidate.consent_at is None:
            candidate.consent_at = datetime.now(timezone.utc)
            candidate.consent_version = "v1"
        if org.retention_days:
            candidate.delete_after = compute_delete_after(org.retention_days)

        key = save_resume(org.id, data, filename)
        app_row = Application(
            org_id=org.id,
            vacancy_id=vacancy_id,
            candidate_id=candidate.id,
            source=ApplicationSource.telegram,
            original_filename=filename,
            file_path=key,
            file_mime=guess_mime(filename, mime),
            status=ApplicationStatus.pending,
        )
        db.add(app_row)
        await db.flush()
        await db.commit()
        await clear_selected_vacancy(org.id, chat_id)

        # Offer to add a cover letter before scoring (it's factored into the AI analysis).
        notice = t(lang, "resume_received")
        if org.privacy_notice:
            notice += f"\n\n{org.privacy_notice}"
        notice += f"\n\n{t(lang, 'cover_ask')}"
        await client.send_message(
            chat_id,
            notice,
            reply_markup={
                "inline_keyboard": [
                    [
                        {"text": t(lang, "btn_add_cover"), "callback_data": f"cover_add_{app_row.id}"},
                        {"text": t(lang, "btn_skip"), "callback_data": f"cover_skip_{app_row.id}"},
                    ]
                ]
            },
        )
        return

    # --- Free-text from a known candidate ---
    # Chat is locked until the recruiter opens it. When locked, reply with a
    # status-aware auto-message and do NOT record the message.
    if text:
        candidate = (
            await db.execute(
                select(Candidate).where(
                    Candidate.org_id == org.id,
                    Candidate.telegram_user_id == tg_user.get("id"),
                )
            )
        ).scalar_one_or_none()
        if candidate:
            latest = (
                await db.execute(
                    select(Application)
                    .where(Application.org_id == org.id, Application.candidate_id == candidate.id)
                    .order_by(Application.created_at.desc())
                    .limit(1)
                )
            ).scalar_one_or_none()
            if latest is not None:
                if latest.stage in (ApplicationStage.rejected, ApplicationStage.withdrawn):
                    await client.send_message(chat_id, t(lang, "chat_rejected"))
                    return
                if not latest.chat_open:
                    await client.send_message(chat_id, t(lang, "chat_locked"))
                    return
                # Chat is open — record the candidate's reply for the recruiter.
                db.add(
                    Message(
                        org_id=org.id,
                        application_id=latest.id,
                        direction=MessageDirection.inbound,
                        body=text,
                        status=MessageStatus.received,
                    )
                )
                await log_activity(
                    db,
                    application=latest,
                    type=ActivityType.message_received,
                    actor=ActivityActor.candidate,
                    summary=text[:120],
                )
                await db.commit()
                return

    # --- Fallback: only respond to strangers (no application yet) ---
    await client.send_message(chat_id, t(lang, "welcome"))
