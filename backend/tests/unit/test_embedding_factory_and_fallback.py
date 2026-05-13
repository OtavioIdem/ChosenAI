import httpx
import pytest

from app.application.services.embeddings.base import EmbeddingDimensionError
from app.application.services.embeddings.factory import build_embedding_provider
from app.application.services.embeddings.fallback_provider import FallbackEmbeddingProvider
from app.application.services.embeddings.hash_provider import HashEmbeddingProvider
from app.application.services.embeddings.ollama_provider import OllamaEmbeddingProvider
from app.config.settings import Settings


def _settings(**overrides):
    data = {
        "embeddings_provider": "hash",
        "embeddings_vector_dimensions": 8,
        "vector_dimensions": 8,
        "embeddings_model": "embeddinggemma",
        "embeddings_base_url": "http://ollama.test",
        "embeddings_timeout_seconds": 1,
        "embeddings_batch_size": 2,
        "embeddings_enable_fallback": True,
        "embeddings_fallback_provider": "hash",
    }
    data.update(overrides)
    return Settings(**data)


def test_factory_returns_hash_provider():
    provider = build_embedding_provider(_settings(embeddings_provider="hash"))
    assert isinstance(provider, HashEmbeddingProvider)


def test_factory_returns_ollama_provider_without_fallback():
    provider = build_embedding_provider(
        _settings(embeddings_provider="ollama", embeddings_enable_fallback=False)
    )
    assert isinstance(provider, OllamaEmbeddingProvider)


def test_factory_wraps_ollama_with_fallback_when_enabled():
    provider = build_embedding_provider(_settings(embeddings_provider="ollama", embeddings_enable_fallback=True))
    assert isinstance(provider, FallbackEmbeddingProvider)


def test_factory_rejects_invalid_provider():
    with pytest.raises(ValueError, match="EMBEDDINGS_PROVIDER inválido"):
        build_embedding_provider(_settings(embeddings_provider="invalid"))


@pytest.mark.asyncio
async def test_fallback_is_used_when_primary_fails():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down")

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(base_url="http://ollama.test", transport=transport)
    primary = OllamaEmbeddingProvider(
        base_url="http://ollama.test",
        model="embeddinggemma",
        dimensions=4,
        timeout_seconds=1,
        batch_size=1,
        client=client,
    )
    provider = FallbackEmbeddingProvider(primary, HashEmbeddingProvider(4), enabled=True)
    try:
        vector = await provider.embed_text("abc")
    finally:
        await client.aclose()

    assert len(vector) == 4
    assert provider.last_fallback_used is True
    assert provider.last_provider_name == "hash"


@pytest.mark.asyncio
async def test_fallback_is_not_used_when_disabled():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down")

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(base_url="http://ollama.test", transport=transport)
    primary = OllamaEmbeddingProvider(
        base_url="http://ollama.test",
        model="embeddinggemma",
        dimensions=4,
        timeout_seconds=1,
        batch_size=1,
        client=client,
    )
    provider = FallbackEmbeddingProvider(primary, HashEmbeddingProvider(4), enabled=False)
    try:
        with pytest.raises(Exception):
            await provider.embed_text("abc")
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_dimension_mismatch_is_not_masked_by_fallback():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"embeddings": [[1, 2]]})

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(base_url="http://ollama.test", transport=transport)
    primary = OllamaEmbeddingProvider(
        base_url="http://ollama.test",
        model="embeddinggemma",
        dimensions=4,
        timeout_seconds=1,
        batch_size=1,
        client=client,
    )
    provider = FallbackEmbeddingProvider(primary, HashEmbeddingProvider(4), enabled=True)
    try:
        with pytest.raises(EmbeddingDimensionError):
            await provider.embed_text("abc")
    finally:
        await client.aclose()
