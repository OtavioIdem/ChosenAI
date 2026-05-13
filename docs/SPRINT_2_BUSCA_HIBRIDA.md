# SAGAI Sprint 2 v1 — Busca Híbrida e Reranking Leve

## Objetivo

A Sprint 2 evolui a qualidade da recuperação do SAGAI após a Sprint 1 de embeddings reais. O foco é reduzir perda de contexto quando a pergunta contém nomes exatos de processos, módulos, telas ou termos operacionais do MaxManager.

## Escopo entregue

- Recuperação híbrida vetorial + lexical.
- Busca full-text PostgreSQL com fallback controlado para `ILIKE` quando necessário.
- Reranking determinístico e transparente.
- Pesos configuráveis por `.env`.
- Filtro mínimo de relevância.
- Telemetria de recuperação no retorno do chat.
- Índices GIN para busca textual.
- Testes unitários para normalização, reranking e combinação de candidatos.
- Ajuste em teste de integração para validar contrato de chat com `retrieval`.

## Arquitetura

Novos módulos:

```txt
backend/app/application/services/retrieval/
  __init__.py
  hybrid_retriever.py
  models.py
  query_analyzer.py
  reranker.py
```

Fluxo:

```txt
ChatService
  -> EmbeddingProvider
  -> HybridRetriever
      -> KnowledgeRepository.search_chunks_vector
      -> KnowledgeRepository.search_chunks_lexical
      -> LightweightReranker
  -> LLMProvider
```

## Configurações

```env
RETRIEVAL_STRATEGY=hybrid
RETRIEVAL_CANDIDATE_MULTIPLIER=4
RETRIEVAL_VECTOR_WEIGHT=0.65
RETRIEVAL_LEXICAL_WEIGHT=0.25
RETRIEVAL_METADATA_WEIGHT=0.10
RETRIEVAL_MIN_SCORE=0.12
RETRIEVAL_ENABLE_RERANKING=true
RETRIEVAL_LEXICAL_LANGUAGE=portuguese
```

## Critérios de qualidade

- A busca vetorial continua funcionando com `embedding_v2`.
- A busca lexical melhora recuperação por termo exato.
- O chat não depende exclusivamente do embedding se a estratégia permitir busca textual.
- A resposta não expõe stacktrace.
- A telemetria permite auditar por que uma fonte foi retornada.

## Limites conhecidos

- O reranker é determinístico e leve; não é um cross-encoder nem um LLM reranker.
- A busca lexical depende do idioma full-text configurado no PostgreSQL.
- A calibração ideal de pesos deve ser feita com dataset real de perguntas do suporte.

## Próximo passo sugerido

Sprint 3: avaliação automática de qualidade RAG com dataset de perguntas esperadas, métricas de precision@k, recall@k, faithfulness e relatório de regressão antes de alterações futuras.
