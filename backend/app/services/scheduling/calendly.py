import hashlib
import hmac

import httpx

API_BASE = "https://api.calendly.com"


class CalendlyError(Exception):
    pass


class CalendlyClient:
    """Minimal Calendly v2 API client using a Personal Access Token."""

    def __init__(self, token: str, timeout: float = 30.0):
        self._token = token
        self._timeout = timeout

    @property
    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"}

    async def _get(self, path: str, params: dict | None = None) -> dict:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.get(f"{API_BASE}{path}", headers=self._headers, params=params)
            if r.status_code >= 400:
                raise CalendlyError(f"GET {path} -> {r.status_code}: {r.text[:300]}")
            return r.json()

    async def me(self) -> dict:
        """Returns the current user resource (uri, current_organization, ...)."""
        return (await self._get("/users/me"))["resource"]

    async def event_types(self, user_uri: str) -> list[dict]:
        data = await self._get("/event_types", {"user": user_uri, "active": "true"})
        return data.get("collection", [])

    async def create_webhook(
        self, url: str, organization_uri: str, signing_key: str
    ) -> dict:
        payload = {
            "url": url,
            "events": ["invitee.created", "invitee.canceled"],
            "organization": organization_uri,
            "scope": "organization",
            "signing_key": signing_key,
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.post(
                f"{API_BASE}/webhook_subscriptions", headers=self._headers, json=payload
            )
            if r.status_code >= 400:
                raise CalendlyError(f"create_webhook -> {r.status_code}: {r.text[:300]}")
            return r.json().get("resource", {})


def verify_signature(signing_key: str, signature_header: str | None, raw_body: bytes) -> bool:
    """Verify a Calendly webhook signature header: `t=<ts>,v1=<hmac>`."""
    if not signature_header or not signing_key:
        return False
    try:
        parts = dict(p.split("=", 1) for p in signature_header.split(","))
        timestamp, sig = parts.get("t"), parts.get("v1")
        if not timestamp or not sig:
            return False
        signed = f"{timestamp}.".encode() + raw_body
        expected = hmac.new(signing_key.encode(), signed, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, sig)
    except Exception:
        return False
