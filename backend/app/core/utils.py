import re
import secrets
import string


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return re.sub(r"-+", "-", value).strip("-") or "org"


def random_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)


_DEEP_LINK_ALPHABET = string.ascii_letters + string.digits


def deep_link_token(length: int = 10) -> str:
    """Short, opaque, unguessable token for vacancy Telegram deep-links.

    Replaces the sequential `job_<id>` so candidates can't enumerate other
    vacancies. Telegram start params allow [A-Za-z0-9_-]; base62 fits.
    """
    return "".join(secrets.choice(_DEEP_LINK_ALPHABET) for _ in range(length))
