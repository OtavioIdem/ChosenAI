from __future__ import annotations

from app.application.services.embeddings.base import EmbeddingProvider
from app.application.services.embeddings.fallback_provider import FallbackEmbeddingProvider
from app.application.services.embeddings.hash_provider import HashEmbeddingProvider
from app.application.services.embeddings.ollama_provider import OllamaEmbeddingProvider
from app.config.settings import Settings, get_settings


def build_embedding_provider(settings: Settings | None = None) -> EmbeddingProvider:
    settings = settings or get_settings()
    provider_name = settings.embeddings_provider.lower().strip()

    if provider_name == "hash":
        return HashEmbeddingProvider(dimensions=settings.embeddings_vector_dimensions)

    if provider_name == "ollama":
        primary = OllamaEmbeddingProvider(
            base_url=settings.embeddings_base_url,
            model=settings.embeddings_model,
            dimensions=settings.embeddings_vector_dimensions,
            timeout_seconds=settings.embeddings_timeout_seconds,
            batch_size=settings.embeddings_batch_size,
        )
        if not settings.embeddings_enable_fallback:
            return primary
        fallback_name = (settings.embeddings_fallback_provider or "hash").lower().strip()
        if fallback_name != "hash":
            raise ValueError(f"Fallback provider inválido para embeddings: {fallback_name!r}.")
        return FallbackEmbeddingProvider(
            primary=primary,
            fallback=HashEmbeddingProvider(dimensions=settings.embeddings_vector_dimensions),
            enabled=True,
        )

    raise ValueError(
        f"EMBEDDINGS_PROVIDER inválido: {settings.embeddings_provider!r}. Valores aceitos: hash, ollama."
    )
