from __future__ import annotations

from app.config.settings import get_settings
from app.infra.llm.base import LLMProvider
from app.infra.llm.mock_provider import MockLLMProvider
from app.infra.llm.ollama_provider import OllamaLLMProvider
from app.infra.llm.openai_compatible_provider import OpenAICompatibleLLMProvider


def build_llm_provider() -> LLMProvider:
    settings = get_settings()
    provider = settings.llm_provider.lower().strip()

    if provider == "mock":
        return MockLLMProvider()

    if provider == "ollama":
        return OllamaLLMProvider()

    if provider == "openai_compatible":
        return OpenAICompatibleLLMProvider()

    raise ValueError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")
