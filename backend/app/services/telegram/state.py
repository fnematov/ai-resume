import redis.asyncio as redis

from app.core.config import settings

_pool: redis.Redis | None = None
_TTL = 60 * 60 * 6  # 6 hours to pick a vacancy and upload


def _client() -> redis.Redis:
    global _pool
    if _pool is None:
        _pool = redis.from_url(settings.redis_url, decode_responses=True)
    return _pool


def _key(org_id: int, chat_id: int) -> str:
    return f"tg:sel:{org_id}:{chat_id}"


async def set_selected_vacancy(org_id: int, chat_id: int, vacancy_id: int) -> None:
    await _client().set(_key(org_id, chat_id), str(vacancy_id), ex=_TTL)


async def get_selected_vacancy(org_id: int, chat_id: int) -> int | None:
    val = await _client().get(_key(org_id, chat_id))
    return int(val) if val else None


async def clear_selected_vacancy(org_id: int, chat_id: int) -> None:
    await _client().delete(_key(org_id, chat_id))


# --- Awaiting test-task submission ---
_SUB_TTL = 60 * 60 * 24 * 14  # 14 days to submit a test task


def _sub_key(org_id: int, chat_id: int) -> str:
    return f"tg:sub:{org_id}:{chat_id}"


async def set_awaiting_submission(org_id: int, chat_id: int, application_id: int) -> None:
    await _client().set(_sub_key(org_id, chat_id), str(application_id), ex=_SUB_TTL)


async def get_awaiting_submission(org_id: int, chat_id: int) -> int | None:
    val = await _client().get(_sub_key(org_id, chat_id))
    return int(val) if val else None


async def clear_awaiting_submission(org_id: int, chat_id: int) -> None:
    await _client().delete(_sub_key(org_id, chat_id))


# --- Awaiting cover letter (text or file) ---
_CL_TTL = 60 * 30  # 30 minutes to add a cover letter after applying


def _cl_key(org_id: int, chat_id: int) -> str:
    return f"tg:cl:{org_id}:{chat_id}"


async def set_awaiting_cover_letter(org_id: int, chat_id: int, application_id: int) -> None:
    await _client().set(_cl_key(org_id, chat_id), str(application_id), ex=_CL_TTL)


async def get_awaiting_cover_letter(org_id: int, chat_id: int) -> int | None:
    val = await _client().get(_cl_key(org_id, chat_id))
    return int(val) if val else None


async def clear_awaiting_cover_letter(org_id: int, chat_id: int) -> None:
    await _client().delete(_cl_key(org_id, chat_id))
