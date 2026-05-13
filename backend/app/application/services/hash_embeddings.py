from __future__ import annotations

import asyncio
from collections.abc import Awaitable

from app.application.services.embeddings.hash_provider import HashEmbeddingProvider
from app.config.settings import get_settings


class HashEmbeddingService:
    """Backward-compatible sync adapter around HashEmbeddingProvider.

    Existing code and older tests imported HashEmbeddingService directly. New code should use
    app.application.services.embeddings.factory.build_embedding_provider instead.
    """

    def __init__(self, dimensions: int | None = None) -> None:
        settings = get_settings()
        self.dimensions = dimensions or settings.embeddings_vector_dimensions
        self.provider = HashEmbeddingProvider(dimensions=self.dimensions)

    def embed_text(self, text: str) -> list[float]:
        return self.provider._embed_text_sync(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(text) for text in texts]


def run_async_blocking(awaitable: Awaitable[list[float]] | Awaitable[list[list[float]]]):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(awaitable)
    raise RuntimeError("Cannot run async embedding operation from an active event loop synchronously.") from None
