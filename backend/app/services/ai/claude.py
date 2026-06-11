import base64

from anthropic import AsyncAnthropic

from app.services.ai.base import (
    SCORE_JSON_SCHEMA,
    AIProvider,
    ResumeDocument,
    ScoreResult,
)

_TOOL_NAME = "submit_assessment"


class ClaudeProvider(AIProvider):
    """Anthropic Claude. Reads PDFs and images natively (no separate OCR)."""

    def _content_blocks(self, document: ResumeDocument) -> list[dict]:
        blocks: list[dict] = []
        if document.is_native and document.data and document.media_type:
            b64 = base64.standard_b64encode(document.data).decode()
            if document.media_type == "application/pdf":
                blocks.append(
                    {
                        "type": "document",
                        "source": {"type": "base64", "media_type": "application/pdf", "data": b64},
                    }
                )
            elif document.media_type.startswith("image/"):
                blocks.append(
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": document.media_type, "data": b64},
                    }
                )
        if document.text:
            blocks.append({"type": "text", "text": f"Resume text:\n\n{document.text}"})
        if not blocks:
            blocks.append({"type": "text", "text": "(No readable resume content was provided.)"})
        blocks.append(
            {
                "type": "text",
                "text": "Assess this resume against the job and call submit_assessment.",
            }
        )
        return blocks

    async def _assess(self, system_prompt: str, document: ResumeDocument) -> ScoreResult:
        client = AsyncAnthropic(api_key=self.api_key)
        try:
            response = await client.messages.create(
                model=self.model,
                max_tokens=1500,
                system=system_prompt,
                tools=[
                    {
                        "name": _TOOL_NAME,
                        "description": "Submit the structured resume assessment.",
                        "input_schema": SCORE_JSON_SCHEMA,
                    }
                ],
                tool_choice={"type": "tool", "name": _TOOL_NAME},
                messages=[{"role": "user", "content": self._content_blocks(document)}],
            )
        finally:
            await client.close()

        for block in response.content:
            if getattr(block, "type", None) == "tool_use" and block.name == _TOOL_NAME:
                return ScoreResult.from_payload(block.input)
        raise RuntimeError("Claude did not return a structured assessment")
