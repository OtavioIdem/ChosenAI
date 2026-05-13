# Sprint 1 — Qualidade da Recuperação

## Entregas

- Interface base `EmbeddingProvider`.
- `HashEmbeddingProvider` determinístico para legado, fallback e CI.
- `OllamaEmbeddingProvider` assíncrono via `/api/embed`.
- Factory configurável por `.env`.
- Fallback controlado para falhas de disponibilidade/timeout/resposta inválida.
- Rejeição explícita de dimensão divergente.
- Reindexação assíncrona com resposta estruturada.
- Logs estruturados de embedding, fallback, reindexação e busca vetorial.
- Coluna `embedding_v2` para preservar a coluna antiga `embedding`.
- Índice HNSW em `embedding_v2` quando suportado pelo pgvector.
- Testes unitários, integração condicional e E2E condicional.

## Arquitetura

Os provedores ficam em:

```text
backend/app/application/services/embeddings/
  base.py
  hash_provider.py
  ollama_provider.py
  fallback_provider.py
  factory.py
```

`ChatService`, `KnowledgeService` e `LearningService` usam a factory para não acoplar regra de negócio ao provider concreto.

## Estratégia de compatibilidade

A coluna `knowledge_chunks.embedding` continua existindo para não destruir dados antigos. A nova coluna `embedding_v2` recebe os embeddings reais na dimensão configurada por `EMBEDDINGS_VECTOR_DIMENSIONS`.

Em ambientes existentes, a função `ensure_pgvector_schema()` cria a coluna e os índices de forma idempotente. Em ambientes novos, `Base.metadata.create_all()` já conhece a coluna mapeada.

## Contrato de reindexação

Campos principais:

- `status`: `success`, `partial_success` ou `error`.
- `provider`: provider configurado.
- `actual_provider`: provider efetivamente usado, útil quando fallback entra.
- `model`: modelo de embeddings.
- `sources_processed` / `sources_failed`.
- `chunks_indexed` / `chunks_failed` / `chunks_ignored`.
- `duration_ms`.
- `errors` sem stacktrace bruto.

## Próximas bases para Sprint 2

- Busca híbrida BM25 + vetorial.
- Métrica de avaliação de recuperação por dataset dourado.
- Reranker leve.
- Job/worker para reindexação fora da requisição HTTP.
- Versionamento de fontes e embeddings.
