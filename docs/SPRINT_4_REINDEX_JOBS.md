# Sprint 4 - Reindexacao Assincrona com Jobs

Esta sprint tira a reindexacao pesada do contrato HTTP sincrono principal e adiciona rastreabilidade persistente para cada execucao.

## Endpoints

Criar job:

```txt
POST /api/v1/knowledge/reindex-jobs
```

Body opcional:

```json
{
  "requested_by": "admin"
}
```

Consultar job:

```txt
GET /api/v1/knowledge/reindex-jobs/{job_id}
```

O endpoint legado continua disponivel:

```txt
POST /api/v1/knowledge/reindex
```

## Status

```txt
pending
running
success
partial_success
failed
cancelled
```

`cancelled` fica reservado para uma sprint futura com cancelamento explicito.

## Progresso persistido

Cada job registra:

```txt
sources_total
sources_processed
sources_failed
chunks_indexed
chunks_failed
chunks_ignored
current_file
duration_ms
error_message
metadata
```

## Banco

Tabela nova:

```txt
reindex_jobs
```

Scripts:

```txt
ops/postgres/init/004-reindex-jobs.sql
ops/postgres/migrations/004-reindex-jobs.sql
```

## Escopo propositalmente simples

A execucao usa `BackgroundTasks` do FastAPI no proprio processo da API. Isso evita Redis/Celery nesta etapa e preserva a arquitetura incremental.

Quando a base crescer, a proxima evolucao natural e mover a execucao para worker dedicado com controle de concorrencia e cancelamento.
