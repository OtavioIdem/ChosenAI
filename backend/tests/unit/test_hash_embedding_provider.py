import pytest

from app.application.services.embeddings.hash_provider import HashEmbeddingProvider


@pytest.mark.asyncio
async def test_hash_embedding_is_deterministic():
    provider = HashEmbeddingProvider(dimensions=32)

    first = await provider.embed_text("Criar usuário no MaxManager")
    second = await provider.embed_text("Criar usuário no MaxManager")

    assert first == second
    assert len(first) == 32


@pytest.mark.asyncio
async def test_hash_embedding_respects_dimension():
    provider = HashEmbeddingProvider(dimensions=11)

    vector = await provider.embed_text("financeiro")

    assert len(vector) == 11


@pytest.mark.asyncio
async def test_hash_embedding_handles_empty_text():
    provider = HashEmbeddingProvider(dimensions=7)

    vector = await provider.embed_text("   ")

    assert vector == [0.0] * 7
