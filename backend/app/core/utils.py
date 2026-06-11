import re
import secrets


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return re.sub(r"-+", "-", value).strip("-") or "org"


def random_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)
