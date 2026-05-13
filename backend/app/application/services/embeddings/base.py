from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from time import perf_counter
from typing import Iterable

logger = logging.getLogger(__name__)


class EmbeddingProviderError(RuntimeError):
    """Base error for controlled embedding failures."""


class EmbeddingProviderUnavailableError(EmbeddingProviderError):
    """Raised when the embedding backend is unavailable."""


class EmbeddingProviderTimeoutError(EmbeddingProviderError):
    """Raised when the embedding backend times out."""


class EmbeddingProviderResponseError(EmbeddingProviderError):
    """Raised when the embedding backend returns an invalid response."""


class EmbeddingDimensionError(EmbeddingProviderError):
    """Raised when an embedding vector does not match the configured dimension."""


@dataclass(frozen=True)
class EmbeddingProviderInfo:
    name: str
    model: str | None
    dimensions: int


class EmbeddingProvider(ABC):
    """Base abstraction for every embedding provider used by SAGAI."""

    name: str
    model: str | None
    dimensions: int

    @abstractmethod
    async def embed_text(self, text: str) -> list[float]:
        raise NotImplementedError

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        started_at = perf_counter()
        vectors = [await self.embed_text(text) for text in texts]
        duration_ms = int((perf_counter() - started_at) * 1000)
        logger.info(
            "embedding_batch_completed",
            extra={
                "provider": self.name,
                "model": self.model,
                "batch_size": len(texts),
                "duration_ms": duration_ms,
            },
        )
        return vectors

    @property
    def info(self) -> EmbeddingProviderInfo:
        return EmbeddingProviderInfo(name=self.name, model=self.model, dimensions=self.dimensions)

    def validate_vector(self, vector: Iterable[float], *, context: str = "embedding") -> list[float]:
        values = [float(value) for value in vector]
        if len(values) != self.dimensions:
            raise EmbeddingDimensionError(
                f"{context} retornou dimensão {len(values)}, esperado {self.dimensions}."
            )
        return values

    def empty_vector(self) -> list[float]:
        return [0.0] * self.dimensions
