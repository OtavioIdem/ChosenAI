# SAGAI — Assistente de IA para MaxManager

SAGAI é um assistente de IA especializado no MaxManager, com backend Python/FastAPI, frontend React, PostgreSQL + pgvector e LLM local via Ollama.

Este pacote contém a estrutura completa consolidada do projeto:

- API de IA em FastAPI.
- Frontend React em estilo chat.
- Banco PostgreSQL com pgvector.
- Base inicial de conhecimento JSON otimizada para MaxManager.
- Prompt principal otimizado.
- Fluxo de feedback, lacunas e treinamento supervisionado.
- Indexação automática de candidatos aprovados.
- Autoaprovação configurável por confiança.
- Provider Ollama validado usando `/api/generate`.
- Ferramenta opcional de scanner de código-fonte.

## 1. Subir o projeto

Copie o `.env.example` para `.env`:

```bash
copy .env.example .env
```

PowerShell:

```powershell
Copy-Item .env.example .env
```

Suba os containers:

```bash
docker compose up -d --build
```

Acesse:

```txt
Frontend: http://localhost:3000
Swagger:  http://localhost:8000/docs
```

## 2. Ollama

Instale o Ollama no Windows e baixe um modelo leve:

```bash
ollama pull llama3.2:1b
```

Teste:

```bash
curl http://localhost:11434/api/tags
```

No `.env`, mantenha:

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama3.2:1b
LLM_TIMEOUT_SECONDS=300
```

## 3. Base de conhecimento

Os JSONs ficam em:

```txt
backend/knowledge/json
```

O prompt fica em:

```txt
backend/knowledge/prompt/system_prompt.md
```

Para reindexar JSONs:

```bash
curl -X POST "http://localhost:8000/api/v1/knowledge/reindex" -H "X-Admin-Key: SUA_ADMIN_API_KEY"
```

## 4. Treinamento

Feedbacks podem criar candidatos de treinamento. Candidatos aprovados viram automaticamente conhecimento indexado.

Aprovar candidato:

```txt
POST /api/v1/training/candidates/{candidate_id}/approve
```

Autoaprovar candidatos com confiança mínima:

```txt
POST /api/v1/training/candidates/auto-approve
```

Body:

```json
{
  "min_confidence": 0.60,
  "reviewed_by": "auto-approve",
  "limit": 100
}
```

## 5. Persistência

O banco usa volume Docker `postgres_data`.

Não rode `docker compose down -v` se quiser preservar dados e treinamentos.

Para rebuildar apenas backend:

```bash
docker compose up -d --build ai-api
```

Para rebuildar apenas frontend:

```bash
docker compose up -d --build frontend
```

## 6. Documentação

Leia também:

```txt
docs/PROJECT_DOCUMENTATION.md
docs/API_REFERENCE.md
docs/ARCHITECTURE.md
BACKEND_TRAINING_INDEXING_README.md
```

## 7. Scanner de código-fonte

Ferramenta opcional:

```txt
tools/source-code-scanner
```

Ela gera um JSON técnico a partir do código-fonte de outro sistema para ser usado como base adicional do SAGAI.

## Sprint 1 — Qualidade da Recuperação

Esta versão adiciona uma camada de provedores de embeddings para melhorar a recuperação RAG sem remover o modo legado.

### Configurar embeddings

Variáveis principais no `.env`:

```env
EMBEDDINGS_PROVIDER=ollama
EMBEDDINGS_MODEL=embeddinggemma
EMBEDDINGS_BASE_URL=http://host.docker.internal:11434
EMBEDDINGS_TIMEOUT_SECONDS=120
EMBEDDINGS_VECTOR_DIMENSIONS=768
EMBEDDINGS_BATCH_SIZE=16
EMBEDDINGS_FALLBACK_PROVIDER=hash
EMBEDDINGS_ENABLE_FALLBACK=true
VECTOR_DIMENSIONS=256
```

Use `EMBEDDINGS_PROVIDER=hash` para desenvolvimento, CI ou quando o Ollama não estiver disponível. Use `EMBEDDINGS_PROVIDER=ollama` para embeddings reais. O modelo de chat continua separado em `LLM_MODEL`.

### Reindexar a base

Com a API rodando:

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/reindex \
  -H "X-Admin-Key: change_this_admin_key"
```

Resposta esperada:

```json
{
  "status": "success",
  "provider": "ollama",
  "actual_provider": "ollama",
  "model": "embeddinggemma",
  "sources_processed": 10,
  "chunks_indexed": 120,
  "chunks_failed": 0,
  "duration_ms": 15320
}
```

Se `EMBEDDINGS_ENABLE_FALLBACK=true` e o Ollama falhar, `actual_provider` pode retornar `hash`. Se o fallback estiver desligado, o erro é controlado e não expõe stacktrace.

### Banco e pgvector

A coluna legada `knowledge_chunks.embedding` foi preservada. A Sprint 1 grava os embeddings reais em `knowledge_chunks.embedding_v2`, criada de forma idempotente em startup para projetos sem Alembic. Também há uma migration SQL em `ops/postgres/migrations/002-embedding-v2-hnsw.sql`.

Para validar se embeddings reais foram usados:

```sql
SELECT COUNT(*) FROM knowledge_chunks WHERE embedding_v2 IS NOT NULL;
```

### Rodar testes

Unitários:

```bash
pytest backend/tests/unit
```

Integração com PostgreSQL + pgvector:

```bash
TEST_DATABASE_URL=postgresql+psycopg://sagai:change_this_password@localhost:5432/sagai_test pytest backend/tests/integration
```

E2E contra API já em execução:

```bash
SAGAI_E2E_BASE_URL=http://localhost:8000 \
SAGAI_E2E_ADMIN_KEY=change_this_admin_key \
pytest backend/tests/e2e
```

### Diagnóstico de falhas no Ollama

1. Confirme se o Ollama está rodando no host.
2. Confirme se `EMBEDDINGS_BASE_URL` aponta para `http://host.docker.internal:11434` quando a API roda em Docker.
3. Confirme se o modelo de embedding está instalado localmente, por exemplo `ollama pull embeddinggemma`.
4. Se o endpoint retornar 404, valide se a versão do Ollama suporta `/api/embed` e se o modelo existe.
5. Para manter o sistema disponível em desenvolvimento, use `EMBEDDINGS_ENABLE_FALLBACK=true`.

## Sprint 2 — Busca Híbrida e Reranking Leve

Esta versão adiciona uma camada de recuperação híbrida para reduzir respostas genéricas e aumentar a chance de recuperar o chunk certo quando a pergunta contém termos exatos do processo.

### Estratégias de recuperação

Variáveis principais no `.env`:

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

Valores aceitos para `RETRIEVAL_STRATEGY`:

- `vector`: usa somente busca vetorial com `embedding_v2`.
- `lexical`: usa somente busca textual/full-text.
- `hybrid`: combina vetorial + lexical, mescla candidatos e aplica reranking determinístico.

### Como funciona

1. O chat gera embedding da pergunta quando o provider estiver disponível.
2. A busca vetorial recupera candidatos por similaridade semântica.
3. A busca lexical recupera candidatos por termos e nomes exatos do processo.
4. O reranker combina `vector_score`, `lexical_score`, `metadata_score` e sobreposição textual.
5. O sistema filtra candidatos abaixo de `RETRIEVAL_MIN_SCORE`.
6. A resposta retorna telemetria em `retrieval` e cada fonte retorna detalhes em `source.retrieval`.

Se o embedding da pergunta falhar e a estratégia permitir, o SAGAI ainda tenta recuperação lexical antes de responder sem contexto.

### Índices de banco

A Sprint 2 adiciona índices GIN para busca textual:

```txt
ops/postgres/migrations/003-hybrid-retrieval-indexes.sql
```

A inicialização da API também tenta criar esses índices de forma idempotente em projetos sem Alembic.

### Validar a Sprint 2

Depois de reindexar a base, execute uma pergunta e confira o bloco `retrieval` no JSON de resposta:

```bash
curl -X POST http://localhost:8000/api/v1/chat/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Como emitir NF-e?","top_k":3}'
```

Resposta esperada inclui:

```json
{
  "retrieval": {
    "strategy": "hybrid",
    "vector_candidates": 12,
    "lexical_candidates": 4,
    "merged_candidates": 14,
    "returned_contexts": 3
  }
}
```

### Testes da Sprint 2

```bash
pytest backend/tests/unit/test_retrieval_query_and_reranker.py
pytest backend/tests/unit
```

Para integração real com PostgreSQL + pgvector:

```bash
TEST_DATABASE_URL=postgresql+psycopg://sagai:change_this_password@localhost:5432/sagai_test pytest backend/tests/integration
```

## Sprint 3 — Avaliacao Automatica de Qualidade RAG

Esta versao adiciona uma primeira suite de avaliacao para medir a qualidade da recuperacao antes de alterar pesos, chunking, modelos ou prompts.

Dataset inicial:

```txt
backend/tests/fixtures/rag_eval_dataset.json
```

Comando a partir do diretorio `backend`:

```bash
python -m app.tools.evaluate_rag --dataset tests/fixtures/rag_eval_dataset.json
```

Metricas geradas:

```txt
precision_at_1
precision_at_3
recall_at_5
mean_reciprocal_rank
no_context_rate
no_relevant_context_rate
expected_no_context_accuracy
avg_retrieval_score
avg_latency_ms
```

Relatorios sao gravados em:

```txt
reports/rag_eval_YYYYMMDD_HHMMSS.md
```

Leia tambem:

```txt
docs/SPRINT_3_AVALIACAO_RAG.md
```

## Sprint 4 — Reindexacao Assincrona com Jobs

Esta versao adiciona jobs persistidos para reindexacao em background, mantendo o endpoint sincrono legado.

Criar job:

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/reindex-jobs \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: change_this_admin_key" \
  -d '{"requested_by":"admin"}'
```

Consultar progresso:

```bash
curl http://localhost:8000/api/v1/knowledge/reindex-jobs/{job_id}
```

O job registra `status`, `sources_total`, `sources_processed`, `chunks_indexed`, `chunks_failed`, `current_file`, `duration_ms` e metadados do provider usado.

Leia tambem:

```txt
docs/SPRINT_4_REINDEX_JOBS.md
```
