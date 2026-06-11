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
from app.services.telegram.state import (
    clear_awaiting_cover_letter,
    clear_awaiting_submission,
    clear_selected_vacancy,
    get_awaiting_cover_letter,
    get_awaiting_submission,
    get_selected_vacancy,
    set_awaiting_cover_letter,
    set_selected_vacancy,
)

WELCOME = (
    "👋 Welcome! Send your resume here (PDF, image, or Word document) "
    "and we'll match it against the role."
)


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


async def _prompt_for_vacancy(client: TelegramClient, chat_id: int, vacancy: Vacancy) -> None:
    await client.send_message(
        chat_id,
        f"You're applying for <b>{vacancy.title}</b>.\n\n{WELCOME}",
    )


async def _upsert_candidate(db: AsyncSession, org_id: int, tg_user: dict) -> Candidate:
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
        )
        db.add(cand)
        await db.flush()
    else:
        cand.telegram_username = tg_user.get("username") or cand.telegram_username
        cand.full_name = full_name or cand.full_name
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
        data = cq.get("data", "")
        await client.answer_callback_query(cq["id"])

        # Cover-letter decision after a resume upload.
        if data.startswith("cover_skip_"):
            try:
                app_id = int(data.rsplit("_", 1)[1])
            except (ValueError, IndexError):
                return
            await clear_awaiting_cover_letter(org.id, chat_id)
            enqueue_score(app_id)
            await client.send_message(
                chat_id, "✅ Thanks! Your application is being reviewed. Good luck! 🍀"
            )
            return
        if data.startswith("cover_add_"):
            try:
                app_id = int(data.rsplit("_", 1)[1])
            except (ValueError, IndexError):
                return
            await set_awaiting_cover_letter(org.id, chat_id, app_id)
            await client.send_message(
                chat_id,
                "✍️ Please send your cover letter now — as a text message or a file. "
                "It will be considered together with your resume.",
            )
            return

        vacancy = await _vacancy_by_param(db, org.id, data)
        if vacancy:
            await set_selected_vacancy(org.id, chat_id, vacancy.id)
            await _prompt_for_vacancy(client, chat_id, vacancy)
        else:
            await client.send_message(chat_id, "That position is no longer open.")
        return

    message = update.get("message")
    if not message:
        return
    chat_id = message["chat"]["id"]
    tg_user = message.get("from", {})
    text = message.get("text", "") or ""

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
            await client.send_message(
                chat_id, "🗑 All your data has been permanently deleted. Take care!"
            )
        else:
            await client.send_message(chat_id, "We have no data stored for you.")
        return

    # --- /start [payload] ---
    if text.startswith("/start"):
        parts = text.split(maxsplit=1)
        payload = parts[1].strip() if len(parts) > 1 else ""
        if payload:
            vacancy = await _vacancy_by_param(db, org.id, payload)
            if vacancy:
                await set_selected_vacancy(org.id, chat_id, vacancy.id)
                await _prompt_for_vacancy(client, chat_id, vacancy)
                return
            await client.send_message(chat_id, "That position is no longer open.")
        vacancies = await _open_vacancies(db, org.id)
        if not vacancies:
            await client.send_message(chat_id, "There are no open positions right now.")
        else:
            await client.send_message(
                chat_id,
                "Please choose the position you're applying for:",
                reply_markup=_vacancy_keyboard(vacancies),
            )
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
            await client.send_message(chat_id, "Please send your cover letter as text or a file.")
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
        await client.send_message(
            chat_id, "✅ Cover letter added — thank you! Your application is being reviewed. 🍀"
        )
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
            await client.send_message(
                chat_id, "✅ Your test task was received — thank you! We'll review it shortly."
            )
            return

        vacancy_id = await get_selected_vacancy(org.id, chat_id)
        if vacancy_id is None:
            vacancies = await _open_vacancies(db, org.id)
            if len(vacancies) == 1:
                vacancy_id = vacancies[0].id
            else:
                await client.send_message(
                    chat_id,
                    "Please choose a position first:",
                    reply_markup=_vacancy_keyboard(vacancies) if vacancies else None,
                )
                return

        # Validate extension
        ext = f".{filename.rsplit('.', 1)[-1].lower()}" if filename and "." in filename else ""
        if ext and ext not in ALLOWED_EXTENSIONS:
            await client.send_message(
                chat_id, "Unsupported file type. Please send a PDF, image, or Word document."
            )
            return

        tg_file = await client.get_file(file_id)
        data = await client.download_file(tg_file["file_path"])
        if len(data) > settings.max_upload_mb * 1024 * 1024:
            await client.send_message(chat_id, "That file is too large.")
            return

        candidate = await _upsert_candidate(db, org.id, tg_user)
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
        notice = "✅ Resume received!"
        if org.privacy_notice:
            notice += f"\n\n{org.privacy_notice}"
        notice += (
            "\n\nWould you like to add a <b>cover letter</b>? It's considered in the AI review "
            "and can strengthen your application."
        )
        await client.send_message(
            chat_id,
            notice,
            reply_markup={
                "inline_keyboard": [
                    [
                        {"text": "✍️ Add cover letter", "callback_data": f"cover_add_{app_row.id}"},
                        {"text": "Skip", "callback_data": f"cover_skip_{app_row.id}"},
                    ]
                ]
            },
        )
        return

    # --- Free-text from a known candidate => inbound message (two-way chat) ---
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
                await client.send_message(
                    chat_id, "Thanks — your message was received. The team will get back to you. 🙌"
                )
                return

    # --- Fallback ---
    await client.send_message(chat_id, WELCOME)
