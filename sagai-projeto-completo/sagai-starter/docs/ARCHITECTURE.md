# SAGAI — Arquitetura Técnica

## Camadas

```txt
frontend/               Interface React
backend/app/api         Rotas FastAPI
backend/app/application Serviços de aplicação
backend/app/core        Prompt, ingestão JSON, chunking
backend/app/infra       Banco, LLM, repositórios
backend/app/domain      Schemas Pydantic
backend/knowledge       Prompt + JSONs de conhecimento
ops/postgres/init       Scripts de inicialização do banco
```

## RAG

1. JSONs são carregados de `backend/knowledge/json`.
2. O backend transforma conteúdo em chunks.
3. Cada chunk recebe embedding via `HashEmbeddingService`.
4. Chunks são salvos no Postgres/pgvector.
5. Perguntas são convertidas em embedding.
6. Os chunks mais próximos são enviados para o LLM.

## LLM

O provider atual usa Ollama:

```txt
POST /api/generate
```

O provider foi implementado em:

```txt
backend/app/infra/llm/ollama_provider.py
```

## Aprendizado supervisionado

O aprendizado não altera o modelo LLM. Ele adiciona conhecimento validado à base vetorial.

Ao aprovar um candidato:

```txt
TrainingCandidate
→ KnowledgeSource
→ KnowledgeChunk
→ Embedding
→ busca futura
```

## Persistência

O banco usa volume Docker nomeado `postgres_data`. Os dados só são apagados se rodar:

```bash
docker compose down -v
```
