import base64
import json

from openai import AsyncOpenAI

from app.services.ai.base import (
    SCORE_JSON_SCHEMA,
    AIProvider,
    ResumeDocument,
    ScoreResult,
)


class OpenAIProvider(AIProvider):
    """OpenAI GPT with vision + JSON-schema structured outputs."""

    def _user_content(self, document: ResumeDocument) -> list[dict]:
        content: list[dict] = [
            {"type": "text", "text": "Assess this resume against the job described in the system prompt."}
        ]
        if document.is_native and document.data and document.media_type:
            b64 = base64.standard_b64encode(document.data).decode()
            if document.media_type.startswith("image/"):
                content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{document.media_type};base64,{b64}"},
                    }
                )
            elif document.media_type == "application/pdf":
                content.append(
                    {
                        "type": "file",
                        "file": {
                            "filename": document.filename or "resume.pdf",
                            "file_data": f"data:application/pdf;base64,{b64}",
                        },
                    }
                )
        if document.text:
            content.append({"type": "text", "text": f"Resume text:\n\n{document.text}"})
        return content

    async def _assess(self, system_prompt: str, document: ResumeDocument) -> ScoreResult:
        client = AsyncOpenAI(api_key=self.api_key)
        try:
            response = await client.chat.completions.create(
                model=self.model,
                # Newer OpenAI models (gpt-4o+, o-series, gpt-5+) use
                # max_completion_tokens; max_tokens is rejected by them.
                max_completion_tokens=4000,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": self._user_content(document)},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "resume_assessment",
                        "strict": True,
                        "schema": SCORE_JSON_SCHEMA,
                    },
                },
            )
        finally:
            await client.close()

        raw = response.choices[0].message.content or "{}"
        return ScoreResult.from_payload(json.loads(raw))

    async def _complete_structured(
        self, system_prompt: str, messages: list[dict], schema: dict, schema_name: str
    ) -> dict:
        client = AsyncOpenAI(api_key=self.api_key)
        try:
            response = await client.chat.completions.create(
                model=self.model,
                max_completion_tokens=4000,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *[{"role": m["role"], "content": m["content"]} for m in messages],
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": schema_name, "strict": True, "schema": schema},
                },
            )
        finally:
            await client.close()

        raw = response.choices[0].message.content or "{}"
        return json.loads(raw)
