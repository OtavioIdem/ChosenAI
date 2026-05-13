from __future__ import annotations

import hashlib
import logging
import math
import re
from time import perf_counter

from app.application.services.embeddings.base import EmbeddingProvider

logger = logging.getLogger(__name__)


class HashEmbeddingProvider(EmbeddingProvider):
    """Deterministic local provider used as legacy mode, fallback and CI-safe provider."""

    name = "hash"

    def __init__(self, dimensions: int) -> None:
        if dimensions <= 0:
            raise ValueError("Embedding dimensions must be greater than 0.")
        self.dimensions = dimensions
        self.model = "deterministic-sha256"

    async def embed_text(self, text: str) -> list[float]:
        return self._embed_text_sync(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        started_at = perf_counter()
        vectors = [self._embed_text_sync(text) for text in texts]
        duration_ms = int((perf_counter() - started_at) * 1000)
        logger.info(
            "hash_embedding_batch_completed",
            extra={"provider": self.name, "batch_size": len(texts), "duration_ms": duration_ms},
        )
        return vectors

    def _embed_text_sync(self, text: str) -> list[float]:
        clean_text = (text or "").strip()
        vector = [0.0] * self.dimensions
        tokens = re.findall(r"\w+", clean_text.lower(), flags=re.UNICODE)

        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            for index in range(self.dimensions):
                value = digest[index % len(digest)]
                weight = ((value % 11) + 1) / 11.0
                vector[index] += weight if value % 2 == 0 else -weight

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]
