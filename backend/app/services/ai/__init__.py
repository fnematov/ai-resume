from app.models.enums import AIProvider as AIProviderEnum
from app.services.ai.base import AIProvider, ResumeDocument, ScoreResult
from app.services.ai.claude import ClaudeProvider
from app.services.ai.openai_provider import OpenAIProvider

DEFAULT_MODELS: dict[AIProviderEnum, str] = {
    AIProviderEnum.claude: "claude-sonnet-4-6",
    AIProviderEnum.openai: "gpt-4o",
}


def get_provider(provider: AIProviderEnum, api_key: str, model: str | None = None) -> AIProvider:
    """Factory: build the right AI provider for an organization's config."""
    chosen_model = model or DEFAULT_MODELS[provider]
    if provider == AIProviderEnum.claude:
        return ClaudeProvider(api_key=api_key, model=chosen_model)
    if provider == AIProviderEnum.openai:
        return OpenAIProvider(api_key=api_key, model=chosen_model)
    raise ValueError(f"Unsupported AI provider: {provider}")


__all__ = [
    "AIProvider",
    "ResumeDocument",
    "ScoreResult",
    "ClaudeProvider",
    "OpenAIProvider",
    "get_provider",
    "DEFAULT_MODELS",
]
