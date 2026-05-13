import httpx
import pytest

from app.application.services.embeddings.base import (
    EmbeddingDimensionError,
    EmbeddingProviderResponseError,
    EmbeddingProviderTimeoutError,
    EmbeddingProviderUnavailableError,
)
from app.application.services.embeddings.ollama_provider import OllamaEmbeddingProvider


def _provider(handler, *, dimensions=3):
    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(base_url="http://ollama.test", transport=transport)
    return OllamaEmbeddingProvider(
        base_url="http://ollama.test",
        model="embeddinggemma",
        dimensions=dimensions,
        timeout_seconds=2,
        batch_size=16,
        client=client,
    ), client


@pytest.mark.asyncio
async def test_ollama_provider_sends_expected_payload():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["payload"] = request.read().decode()
        return httpx.Response(200, json={"embeddings": [[0.1, 0.2, 0.3]]})

    provider, client = _provider(handler)
    try:
        vector = await provider.embed_text("teste")
    finally:
        await client.aclose()

    assert seen["path"] == "/api/embed"
    assert '"model":"embeddinggemma"' in seen["payload"].replace(" ", "")
    assert '"input":["teste"]' in seen["payload"].replace(" ", "")
    assert vector == [0.1, 0.2, 0.3]


@pytest.mark.asyncio
async def test_ollama_provider_handles_valid_response():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"embeddings": [[1, 2, 3], [4, 5, 6]]})

    provider, client = _provider(handler)
    try:
        vectors = await provider.embed_batch(["a", "b"])
    finally:
        await client.aclose()

    assert vectors == [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]


@pytest.mark.asyncio
async def test_ollama_provider_handles_timeout():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timeout")

    provider, client = _provider(handler)
    try:
        with pytest.raises(EmbeddingProviderTimeoutError):
            await provider.embed_text("a")
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_ollama_provider_handles_connection_refused():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    provider, client = _provider(handler)
    try:
        with pytest.raises(EmbeddingProviderUnavailableError):
            await provider.embed_text("a")
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_ollama_provider_handles_404():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": "not found"})

    provider, client = _provider(handler)
    try:
        with pytest.raises(EmbeddingProviderUnavailableError):
            await provider.embed_text("a")
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_ollama_provider_rejects_missing_embedding():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True})

    provider, client = _provider(handler)
    try:
        with pytest.raises(EmbeddingProviderResponseError):
            await provider.embed_text("a")
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_ollama_provider_rejects_dimension_mismatch():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"embeddings": [[1, 2]]})

    provider, client = _provider(handler, dimensions=3)
    try:
        with pytest.raises(EmbeddingDimensionError):
            await provider.embed_text("a")
    finally:
        await client.aclose()
