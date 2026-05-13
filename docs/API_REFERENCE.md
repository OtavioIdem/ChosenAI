# SAGAI — API Reference

Base URL local:

```txt
http://localhost:8000
```

Swagger:

```txt
http://localhost:8000/docs
```

## Health

```txt
GET /health/liveness
GET /health/readiness
```

## Chat

```txt
POST /api/v1/chat/ask
```

Body:

```json
{
  "question": "Como emitir uma NF-e no MaxManager?",
  "top_k": 5,
  "session_id": null,
  "user_identifier": "suporte"
}
```

## Knowledge

```txt
GET  /api/v1/knowledge/stats
POST /api/v1/knowledge/reindex
```

`POST /knowledge/reindex` exige header:

```txt
X-Admin-Key: SUA_ADMIN_API_KEY
```

## Feedback

```txt
POST /api/v1/feedback
```

Body:

```json
{
  "message_id": "uuid-da-mensagem",
  "rating": "useful",
  "comment": "Resposta ajudou.",
  "created_by": "suporte",
  "create_training_candidate": true
}
```

Ratings aceitos:

```txt
useful
not_useful
incomplete
incorrect
bad_source
needs_adjustment
```

## Lacunas

```txt
GET  /api/v1/knowledge/gaps
POST /api/v1/knowledge/gaps/{gap_id}/resolve
```

## Treinamento

```txt
GET  /api/v1/training/candidates
PUT  /api/v1/training/candidates/{candidate_id}
POST /api/v1/training/candidates/{candidate_id}/approve
POST /api/v1/training/candidates/{candidate_id}/reject
POST /api/v1/training/candidates/auto-approve
```

Autoaprovação:

```json
{
  "min_confidence": 0.60,
  "reviewed_by": "auto-approve",
  "limit": 100
}
```

### Resposta do chat com telemetria de recuperação

A Sprint 2 adiciona o campo `retrieval` no retorno de `POST /api/v1/chat/ask` e em cada fonte retornada.

Exemplo parcial:

```json
{
  "answer": "...",
  "confidence_score": 0.74,
  "confidence_status": "medium",
  "retrieval": {
    "strategy": "hybrid",
    "vector_candidates": 12,
    "lexical_candidates": 4,
    "merged_candidates": 14,
    "returned_contexts": 3,
    "duration_ms": 42
  },
  "sources": [
    {
      "title": "NF-e",
      "source_identifier": "json/categorias/nf_e.sagai.json",
      "chunk_index": 0,
      "score": 0.81,
      "retrieval": {
        "vector_score": 0.78,
        "lexical_score": 1.0,
        "metadata_score": 0.5,
        "match_types": ["lexical", "vector"]
      }
    }
  ]
}
```
