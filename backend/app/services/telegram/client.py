import httpx

API_BASE = "https://api.telegram.org"


class TelegramError(Exception):
    pass


class TelegramClient:
    """Minimal async Telegram Bot API client bound to a single org's bot token."""

    def __init__(self, token: str, timeout: float = 30.0):
        self._token = token
        self._timeout = timeout

    @property
    def _api(self) -> str:
        return f"{API_BASE}/bot{self._token}"

    @property
    def _file_api(self) -> str:
        return f"{API_BASE}/file/bot{self._token}"

    async def _call(self, method: str, payload: dict | None = None) -> dict:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(f"{self._api}/{method}", json=payload or {})
            data = resp.json()
            if not data.get("ok"):
                raise TelegramError(f"{method} failed: {data.get('description')}")
            return data["result"]

    async def get_me(self) -> dict:
        return await self._call("getMe")

    async def set_webhook(self, url: str, secret_token: str) -> dict:
        return await self._call(
            "setWebhook",
            {
                "url": url,
                "secret_token": secret_token,
                "allowed_updates": ["message", "callback_query"],
                "drop_pending_updates": True,
            },
        )

    async def delete_webhook(self) -> dict:
        return await self._call("deleteWebhook", {"drop_pending_updates": False})

    async def send_message(
        self, chat_id: int, text: str, reply_markup: dict | None = None
    ) -> dict:
        payload: dict = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return await self._call("sendMessage", payload)

    async def send_document(
        self, chat_id: int, file_bytes: bytes, filename: str, caption: str | None = None
    ) -> dict:
        data: dict = {"chat_id": str(chat_id)}
        if caption:
            data["caption"] = caption
            data["parse_mode"] = "HTML"
        files = {"document": (filename, file_bytes)}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(f"{self._api}/sendDocument", data=data, files=files)
            payload = resp.json()
            if not payload.get("ok"):
                raise TelegramError(f"sendDocument failed: {payload.get('description')}")
            return payload["result"]

    async def answer_callback_query(self, callback_query_id: str, text: str | None = None) -> dict:
        payload: dict = {"callback_query_id": callback_query_id}
        if text:
            payload["text"] = text
        return await self._call("answerCallbackQuery", payload)

    async def get_file(self, file_id: str) -> dict:
        return await self._call("getFile", {"file_id": file_id})

    async def download_file(self, file_path: str) -> bytes:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(f"{self._file_api}/{file_path}")
            resp.raise_for_status()
            return resp.content
