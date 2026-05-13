from __future__ import annotations

import logging

from app.application.services.embeddings.base import (
    EmbeddingDimensionError,
    EmbeddingProvider,
    EmbeddingProviderError,
    EmbeddingProviderResponseError,
    EmbeddingProviderTimeoutError,
    EmbeddingProviderUnavailableError,
)

logger = logging.getLogger(__name__)

_FALLBACKABLE_ERRORS = (
    EmbeddingProviderUnavailableError,
    EmbeddingProviderTimeoutError,
    EmbeddingProviderResponseError,
)


class FallbackEmbeddingProvider(EmbeddingProvider):
    """Wraps a primary provider and falls back only for backend availability/response failures."""

    def __init__(self, primary: EmbeddingProvider, fallback: EmbeddingProvider, *, enabled: bool) -> None:
        if primary.dimensions != fallback.dimensions:
            raise ValueError("Primary and fallback embedding providers must use the same dimensions.")
        self.primary = primary
        self.fallback = fallback
        self.enabled = enabled
        self.name = primary.name
        self.model = primary.model
        self.dimensions = primary.dimensions
        self.last_provider_name = primary.name
        self.last_fallback_used = False

    async def embed_text(self, text: str) -> list[float]:
        vectors = await self.embed_batch([text])
        return vectors[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        self.last_provider_name = self.primary.name
        self.last_fallback_used = False
        try:
            return await self.primary.embed_batch(texts)
        except EmbeddingDimensionError:
            # Never mask a wrong vector dimension with fallback; it can corrupt pgvector state.
            raise
        except _FALLBACKABLE_ERRORS as exc:
            if not self.enabled:
                raise
            logger.warning(
                "embedding_fallback_used",
                extra={
                    "primary_provider": self.primary.name,
                    "fallback_provider": self.fallback.name,
                    "error_type": type(exc).__name__,
                },
            )
            self.last_provider_name = self.fallback.name
            self.last_fallback_used = True
            return await self.fallback.embed_batch(texts)
        except EmbeddingProviderError:
            raise
