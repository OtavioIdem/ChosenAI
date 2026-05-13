from types import SimpleNamespace
from uuid import uuid4

from app.application.services.retrieval.hybrid_retriever import HybridRetriever
from app.application.services.retrieval.query_analyzer import extract_query_terms, normalize_query
from app.application.services.retrieval.reranker import LightweightReranker
from app.application.services.retrieval.models import RetrievalCandidate
from app.config.settings import Settings


def _settings(**overrides):
    data = {
        "embeddings_vector_dimensions": 4,
        "vector_dimensions": 4,
        "retrieval_strategy": "hybrid",
        "retrieval_candidate_multiplier": 3,
        "retrieval_vector_weight": 0.60,
        "retrieval_lexical_weight": 0.30,
        "retrieval_metadata_weight": 0.10,
        "retrieval_min_score": 0.0,
        "retrieval_enable_reranking": True,
        "retrieval_lexical_language": "portuguese",
    }
    data.update(overrides)
    return Settings(**data)


def _chunk(content, *, metadata=None):
    return SimpleNamespace(
        id=uuid4(),
        content=content,
        chunk_index=0,
        chunk_metadata=metadata or {},
    )


def _source(title="Fonte", category="financeiro"):
    return SimpleNamespace(
        title=title,
        category=category,
        source_identifier=f"test/{title}.json",
    )


def test_query_analyzer_normalizes_accents_and_stopwords():
    assert normalize_query("Emissão de NF-e no MáxManager!") == "emissao de nf-e no maxmanager"
    terms = extract_query_terms("Como emitir uma NF-e no módulo Fiscal?")
    assert "emitir" in terms
    assert "fiscal" in terms
    assert "como" not in terms


def test_lightweight_reranker_prefers_exact_lexical_match():
    source = _source(title="Processo ALFA", category="testes")
    exact = RetrievalCandidate(
        chunk=_chunk("Para concluir o processo ALFA, acesse Testes > Processo ALFA."),
        source=source,
        vector_score=0.50,
        lexical_score=1.0,
        match_types={"lexical"},
    )
    generic = RetrievalCandidate(
        chunk=_chunk("Conteúdo genérico sobre processos."),
        source=source,
        vector_score=0.70,
        lexical_score=0.0,
        match_types={"vector"},
    )
    reranker = LightweightReranker(
        vector_weight=0.60,
        lexical_weight=0.30,
        metadata_weight=0.10,
        enable_reranking=True,
    )

    ranked = reranker.rerank("Como concluir o processo ALFA?", [generic, exact])

    assert ranked[0] is exact
    assert ranked[0].final_score > ranked[1].final_score
    assert "correspondencia_lexical" in ranked[0].rank_reasons


def test_hybrid_retriever_merges_vector_and_lexical_candidates():
    source = _source(title="Processo ALFA", category="testes")
    chunk_vector = _chunk("Conteúdo aproximado sobre testes.")
    chunk_lexical = _chunk("Para concluir o processo ALFA, acesse Testes > Processo ALFA.")

    class FakeRepository:
        def search_chunks_vector(self, query_embedding, limit):
            return [(chunk_vector, source, 0.25)]

        def search_chunks_lexical(self, *, query_text, limit, language):
            return [(chunk_lexical, source, 2.0)]

    retriever = HybridRetriever(FakeRepository(), _settings())
    contexts = retriever.retrieve(query="processo ALFA", query_embedding=[0.1, 0.2, 0.3, 0.4], top_k=2)

    assert len(contexts) == 2
    assert contexts[0].metadata["retrieval"]["strategy"] == "hybrid"
    assert retriever.last_telemetry is not None
    assert retriever.last_telemetry.vector_candidates == 1
    assert retriever.last_telemetry.lexical_candidates == 1


def test_hybrid_retriever_can_use_lexical_when_embedding_is_unavailable():
    source = _source(title="Financeiro", category="financeiro")
    chunk_lexical = _chunk("Baixa de contas a receber no financeiro.")

    class FakeRepository:
        def search_chunks_vector(self, query_embedding, limit):
            raise AssertionError("vector branch should not run without embedding")

        def search_chunks_lexical(self, *, query_text, limit, language):
            return [(chunk_lexical, source, 1.0)]

    retriever = HybridRetriever(FakeRepository(), _settings())
    contexts = retriever.retrieve(query="contas a receber", query_embedding=None, top_k=1)

    assert len(contexts) == 1
    assert contexts[0].metadata["retrieval"]["match_types"] == ["lexical"]
