from __future__ import annotations

import hashlib
import math
import re

from app.config.settings import get_settings


class HashEmbeddingService:
    def __init__(self, dimensions: int | None = None) -> None:
        settings = get_settings()
        self.dimensions = dimensions or settings.vector_dimensions

    def embed_text(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = re.findall(r"\w+", text.lower(), flags=re.UNICODE)

        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            for index in range(0, min(len(digest), self.dimensions)):
                value = digest[index]
                vector[index] += 1.0 if value % 2 == 0 else -1.0

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector

        return [value / norm for value in vector]
