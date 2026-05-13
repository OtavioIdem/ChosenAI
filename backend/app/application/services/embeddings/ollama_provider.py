from __future__ import annotations

import logging
from time import perf_counter
from typing import Any

import httpx

from app.application.services.embeddings.base import (
    EmbeddingDimensionError,
    EmbeddingProvider,
    EmbeddingProviderResponseError,
    EmbeddingProviderTimeoutError,
    EmbeddingProviderUnavailableError,
)

logger = logging.getLogger(__name__)


class OllamaEmbeddingProvider(EmbeddingProvider):
    """Embedding provider backed by Ollama's local HTTP API."""

    name = "ollama"

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        dimensions: int,
        timeout_seconds: float,
        batch_size: int,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not base_url:
            raise ValueError("Ollama embeddings base URL is required.")
        if not model:
            raise ValueError("Ollama embeddings model is required.")
        if dimensions <= 0:
            raise ValueError("Embedding dimensions must be greater than 0.")
        if batch_size <= 0:
            raise ValueError("Embedding batch size must be greater than 0.")

        self.base_url = base_url.rstrip("/")
        self.model = model
        self.dimensions = dimensions
        self.timeout_seconds = timeout_seconds
        self.batch_size = batch_size
        self._client = client

    async def embed_text(self, text: str) -> list[float]:
        vectors = await self.embed_batch([text])
        return vectors[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        all_vectors: list[list[float]] = []
        for start in range(0, len(texts), self.batch_size):
            batch = texts[start : start + self.batch_size]
            all_vectors.extend(await self._embed_batch_once(batch))
        return all_vectors

    async def _embed_batch_once(self, texts: list[str]) -> list[list[float]]:
        if all(not (text or "").strip() for text in texts):
            return [self.empty_vector() for _ in texts]

        payload = {"model": self.model, "input": [text or "" for text in texts]}
        started_at = perf_counter()

        close_client = False
        client = self._client
        if client is None:
            client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout_seconds)
            close_client = True

        try:
            response = await client.post("/api/embed", json=payload)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            logger.warning(
                "ollama_embedding_timeout",
                extra={"provider": self.name, "model": self.model, "batch_size": len(texts)},
            )
            raise EmbeddingProviderTimeoutError("Timeout ao gerar embeddings no Ollama.") from exc
        except httpx.ConnectError as exc:
            logger.warning(
                "ollama_embedding_connection_error",
                extra={"provider": self.name, "model": self.model, "base_url": self.base_url},
            )
            raise EmbeddingProviderUnavailableError("Ollama indisponível para embeddings.") from exc
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            logger.warning(
                "ollama_embedding_http_error",
                extra={"provider": self.name, "model": self.model, "status_code": status_code},
            )
            if status_code == 404:
                raise EmbeddingProviderUnavailableError(
                    "Endpoint de embeddings do Ollama não encontrado ou modelo indisponível."
                ) from exc
            if status_code and status_code >= 500:
                raise EmbeddingProviderUnavailableError("Ollama retornou erro interno ao gerar embeddings.") from exc
            raise EmbeddingProviderResponseError("Ollama retornou erro HTTP ao gerar embeddings.") from exc
        except httpx.HTTPError as exc:
            logger.warning(
                "ollama_embedding_http_client_error",
                extra={"provider": self.name, "model": self.model, "error_type": type(exc).__name__},
            )
            raise EmbeddingProviderUnavailableError("Falha de comunicação com Ollama para embeddings.") from exc
        finally:
            if close_client:
                await client.aclose()

        duration_ms = int((perf_counter() - started_at) * 1000)
        data = self._parse_json(response)
        vectors = self._extract_vectors(data, expected_count=len(texts))
        logger.info(
            "ollama_embedding_batch_completed",
            extra={
                "provider": self.name,
                "model": self.model,
                "batch_size": len(texts),
                "dimensions": self.dimensions,
                "duration_ms": duration_ms,
            },
        )
        return vectors

    def _parse_json(self, response: httpx.Response) -> dict[str, Any]:
        try:
            data = response.json()
        except ValueError as exc:
            raise EmbeddingProviderResponseError("Resposta inválida do Ollama: JSON malformado.") from exc
        if not isinstance(data, dict):
            raise EmbeddingProviderResponseError("Resposta inválida do Ollama: objeto JSON esperado.")
        return data

    def _extract_vectors(self, data: dict[str, Any], *, expected_count: int) -> list[list[float]]:
        # Current Ollama /api/embed response: {"embeddings": [[...], ...]}
        raw_embeddings = data.get("embeddings")
        if raw_embeddings is None and "embedding" in data:
            # Legacy /api/embeddings shape, kept for defensive parsing and tests.
            raw_embeddings = [data["embedding"]]

        if not isinstance(raw_embeddings, list) or not raw_embeddings:
            raise EmbeddingProviderResponseError("Resposta do Ollama sem embeddings.")

        if raw_embeddings and raw_embeddings and all(isinstance(item, (int, float)) for item in raw_embeddings):
            raw_embeddings = [raw_embeddings]

        if len(raw_embeddings) != expected_count:
            raise EmbeddingProviderResponseError(
                f"Ollama retornou {len(raw_embeddings)} embeddings para {expected_count} textos."
            )

        vectors: list[list[float]] = []
        for index, vector in enumerate(raw_embeddings):
            if not isinstance(vector, list) or not vector:
                raise EmbeddingProviderResponseError("Embedding vazio retornado pelo Ollama.")
            try:
                vectors.append(self.validate_vector(vector, context=f"embedding[{index}]"))
            except EmbeddingDimensionError:
                logger.warning(
                    "ollama_embedding_dimension_mismatch",
                    extra={
                        "provider": self.name,
                        "model": self.model,
                        "expected_dimensions": self.dimensions,
                        "returned_dimensions": len(vector),
                    },
                )
                raise
        return vectors
