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
