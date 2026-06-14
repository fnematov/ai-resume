import uuid
from pathlib import Path

from app.core.config import settings


def _base_dir() -> Path:
    base = Path(settings.storage_dir)
    base.mkdir(parents=True, exist_ok=True)
    return base


def save_resume(org_id: int, data: bytes, filename: str | None) -> str:
    """Persist resume bytes to local storage; return a relative path key.

    Abstraction point: swap this module's body for S3/MinIO later without
    touching callers.
    """
    suffix = Path(filename).suffix.lower() if filename else ""
    key = f"org_{org_id}/{uuid.uuid4().hex}{suffix}"
    dest = _base_dir() / key
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return key


def save_image(org_id: int, data: bytes, filename: str | None) -> str:
    """Persist a vacancy banner image; return a relative path key."""
    suffix = Path(filename).suffix.lower() if filename else ""
    key = f"org_{org_id}/vacancy_images/{uuid.uuid4().hex}{suffix}"
    dest = _base_dir() / key
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return key


def read_file(key: str) -> bytes:
    return (_base_dir() / key).read_bytes()


def file_exists(key: str) -> bool:
    return (_base_dir() / key).exists()


def delete_file(key: str | None) -> None:
    if not key:
        return
    try:
        (_base_dir() / key).unlink(missing_ok=True)
    except Exception:
        pass


# Resume-specific aliases (kept for existing callers).
def read_resume(key: str) -> bytes:
    return (_base_dir() / key).read_bytes()


def resume_exists(key: str) -> bool:
    return (_base_dir() / key).exists()


def delete_resume(key: str | None) -> None:
    delete_file(key)
