# Sprint 3 - Avaliacao Automatica de Qualidade RAG

Esta sprint adiciona uma primeira suite objetiva para medir a qualidade da recuperacao RAG antes de alterar pesos, chunking, modelos ou prompts.

## Comando

Executar a partir do diretorio `backend`:

```bash
python -m app.tools.evaluate_rag --dataset tests/fixtures/rag_eval_dataset.json
```

Ou, a partir da raiz do repositorio com `PYTHONPATH=backend`:

```bash
python -m app.tools.evaluate_rag --dataset backend/tests/fixtures/rag_eval_dataset.json
```

Para reindexar antes da avaliacao:

```bash
python -m app.tools.evaluate_rag --dataset tests/fixtures/rag_eval_dataset.json --reindex
```

## Saida

O comando gera um relatorio Markdown em:

```txt
reports/rag_eval_YYYYMMDD_HHMMSS.md
```

## Metricas

- `precision_at_1`
- `precision_at_3`
- `recall_at_5`
- `mean_reciprocal_rank`
- `no_context_rate`
- `no_relevant_context_rate`
- `expected_no_context_accuracy`
- `avg_retrieval_score`
- `avg_latency_ms`

## Dataset

O dataset inicial fica em:

```txt
backend/tests/fixtures/rag_eval_dataset.json
```

Cada pergunta declara fontes esperadas por `expected_source_identifiers`, `expected_source_files` ou marca `expected_no_context=true` para perguntas negativas.
