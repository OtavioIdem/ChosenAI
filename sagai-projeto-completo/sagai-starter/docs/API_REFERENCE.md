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
