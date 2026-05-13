# SAGAI — Treinamento aprovado com indexação automática

Esta versão corrige o fluxo de aprendizado supervisionado.

Antes:

```txt
feedback/candidato → approve → apenas mudava status
```

Agora:

```txt
feedback/candidato → approve → cria KnowledgeSource → cria KnowledgeChunks → status indexed
```

Ou seja: depois de aprovar um candidato, ele passa a ser pesquisável pelo RAG na próxima pergunta.

## Novidades

### 1. Aprovação individual com indexação

Endpoint já existente:

```txt
POST /api/v1/training/candidates/{candidate_id}/approve
```

Agora ele também indexa o conteúdo aprovado.

O candidato usa, nesta ordem:

```txt
corrected_answer, se existir
senão generated_answer
```

O conteúdo indexado inclui:

```txt
- pergunta original
- resposta aprovada
- conteúdo de referência, se existir
- URL fonte, se existir
- módulo sugerido
- palavras-chave
```

Depois de aprovado, o status vira:

```txt
indexed
```

---

### 2. Aprovação automática por confiança

Novo endpoint:

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

Se `min_confidence` vier `null` ou for omitido, usa o valor do `.env`:

```env
TRAINING_AUTO_APPROVE_MIN_CONFIDENCE=0.60
```

Esse endpoint busca candidatos com status:

```txt
pending
edited
```

e com:

```txt
confidence_score >= min_confidence
```

Depois aprova e indexa em lote.

---

## Variável nova

Adicione no `.env`:

```env
TRAINING_AUTO_APPROVE_MIN_CONFIDENCE=0.60
```

Quando o SAGAI evoluir, você pode subir para:

```env
TRAINING_AUTO_APPROVE_MIN_CONFIDENCE=0.70
TRAINING_AUTO_APPROVE_MIN_CONFIDENCE=0.80
TRAINING_AUTO_APPROVE_MIN_CONFIDENCE=0.90
```

---

## Como validar que funcionou

1. Veja stats antes:

```bash
curl http://localhost:8000/api/v1/knowledge/stats
```

2. Aprove um candidato:

```bash
curl -X POST "http://localhost:8000/api/v1/training/candidates/SEU_ID/approve" \
  -H "Content-Type: application/json" \
  -d "{\"reviewed_by\":\"otavio\"}"
```

3. Veja stats depois:

```bash
curl http://localhost:8000/api/v1/knowledge/stats
```

Agora deve aumentar pelo menos:

```txt
sources_count +1
chunks_count +1 ou mais
```

4. Faça a mesma pergunta no chat.

A resposta deve vir com score melhor e fonte parecida com:

```txt
training/candidates/{candidate_id}.sagai.json
```

---

## Importante

Não precisa rodar `/api/v1/knowledge/reindex` para candidatos aprovados.

O endpoint de approve já indexa diretamente no banco vetorial.

Use `/api/v1/knowledge/reindex` apenas quando alterar arquivos JSON em:

```txt
backend/knowledge/json
```
