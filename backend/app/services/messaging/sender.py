from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_secret
from app.models import (
    ActivityActor,
    ActivityType,
    Application,
    Candidate,
    Message,
    MessageDirection,
    MessageStatus,
    Organization,
)
from app.services.activities import log_activity
from app.services.telegram.client import TelegramClient, TelegramError


async def send_to_candidate(
    db: AsyncSession,
    application: Application,
    body: str,
    *,
    sent_by_user_id: int | None = None,
    template_id: int | None = None,
    document: tuple[bytes, str] | None = None,
    activity_type: ActivityType = ActivityType.message_sent,
    activity_summary: str | None = None,
    actor: ActivityActor = ActivityActor.user,
) -> Message:
    """Send a Telegram message (optionally with a document) to the application's candidate.

    Records a Message row and a timeline Activity. Does NOT commit — caller controls the txn.
    """
    org = await db.get(Organization, application.org_id)
    candidate = (
        await db.get(Candidate, application.candidate_id) if application.candidate_id else None
    )

    msg = Message(
        org_id=application.org_id,
        application_id=application.id,
        direction=MessageDirection.outbound,
        body=body,
        template_id=template_id,
        sent_by_user_id=sent_by_user_id,
        status=MessageStatus.sent,
    )

    chat_id = candidate.telegram_user_id if candidate else None
    if not org or not org.telegram_bot_token_enc or not chat_id:
        msg.status = MessageStatus.failed
        msg.error = "No Telegram bot configured or candidate has no Telegram id"
    else:
        client = TelegramClient(decrypt_secret(org.telegram_bot_token_enc))
        try:
            if document is not None:
                data, filename = document
                result = await client.send_document(chat_id, data, filename, caption=body or None)
            else:
                result = await client.send_message(chat_id, body)
            msg.telegram_message_id = result.get("message_id")
        except TelegramError as exc:
            msg.status = MessageStatus.failed
            msg.error = str(exc)[:1000]

    db.add(msg)
    await log_activity(
        db,
        application=application,
        type=activity_type,
        actor=actor,
        actor_user_id=sent_by_user_id,
        summary=activity_summary or (body[:120] if body else "Message sent"),
    )
    return msg
