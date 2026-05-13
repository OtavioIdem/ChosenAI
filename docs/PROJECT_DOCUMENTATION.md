# SAGAI — Documentação do Projeto

## 1. Visão geral

O SAGAI é um assistente de inteligência artificial especializado no ecossistema MaxManager. O projeto foi criado para auxiliar usuários, suporte e desenvolvedores na compreensão e execução de processos do sistema, como NF-e, SPED, fiscal, financeiro, estoque, cadastros, faturamento, tributação e demais rotinas operacionais.

O objetivo não é construir uma IA genérica ou treinar uma rede neural do zero. O SAGAI usa uma arquitetura baseada em RAG, ou seja, ele recupera trechos de conhecimento da base documental interna e envia esse contexto para um modelo local de linguagem. Isso permite respostas mais controladas, auditáveis e baratas do que depender de uma IA sem contexto ou de fine-tuning prematuro.

A primeira fase do projeto foi pensada para uso interno por suporte e desenvolvedores. Esse ambiente controlado permite testar perguntas reais, avaliar respostas, gerar lacunas de conhecimento e transformar interações validadas em novos conteúdos indexados.

## 2. Arquitetura geral

A estrutura atual é composta por:

- Frontend em React + Vite.
- Backend em Python + FastAPI.
- Banco PostgreSQL com extensão pgvector.
- Ollama local como provedor LLM.
- Base documental em JSON otimizado.
- Prompt principal versionado em arquivo.
- Fluxo de feedback, lacunas e candidatos de treinamento.
- Indexação automática de candidatos aprovados.

Fluxo principal:

```txt
Usuário pergunta
→ Frontend envia para API
→ Backend salva mensagem
→ Backend busca chunks relevantes no Postgres/pgvector
→ Backend monta prompt com contexto RAG
→ Backend chama Ollama via /api/generate
→ Resposta retorna ao usuário
→ Usuário avalia
→ Feedback pode criar candidato de treinamento
→ Candidato aprovado vira knowledge_source + knowledge_chunk
→ SAGAI passa a usar esse conteúdo em respostas futuras
```

## 3. Estratégia de IA

A estratégia adotada é RAG + aprendizado supervisionado.

O SAGAI não “aprende” diretamente dentro do modelo LLM. Ele melhora porque novos conteúdos aprovados entram na base vetorial. Essa abordagem é mais segura porque evita que respostas incorretas sejam absorvidas automaticamente.

O ciclo de melhoria é:

```txt
Pergunta real
→ resposta gerada
→ feedback do usuário
→ candidato de treinamento
→ auditoria ou autoaprovação controlada
→ indexação
→ nova resposta com melhor contexto
```

## 4. Modelo local

O provedor atual é Ollama. Durante os testes, modelos 8B deixaram a máquina pesada ou retornaram erro por falta de memória. O modelo recomendado para desenvolvimento é:

```env
OLLAMA_MODEL=llama3.2:1b
```

Ele é mais leve e permite validar o fluxo completo do SAGAI. Em máquinas com mais memória, é possível trocar para modelos maiores.

## 5. Variáveis principais

Arquivo: `.env`

```env
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2:1b
LLM_BASE_URL=http://host.docker.internal:11434
LLM_TIMEOUT_SECONDS=300
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama3.2:1b
TRAINING_AUTO_APPROVE_MIN_CONFIDENCE=0.60
ADMIN_API_KEY=change_this_admin_key
```

O `host.docker.internal` é usado porque o backend roda dentro do Docker e o Ollama roda diretamente no Windows.

## 6. Base de conhecimento

A base inicial fica em:

```txt
backend/knowledge/json
```

O prompt principal fica em:

```txt
backend/knowledge/prompt/system_prompt.md
```

A base otimizada do MaxManager já está incluída neste pacote em subpastas como:

```txt
backend/knowledge/json/categorias
backend/knowledge/json/especiais
```

## 7. Reindexação

Quando novos JSONs forem adicionados manualmente:

```bash
curl -X POST "http://localhost:8000/api/v1/knowledge/reindex" -H "X-Admin-Key: SUA_ADMIN_API_KEY"
```

Quando um candidato de treinamento é aprovado pelo endpoint de treinamento, ele já é transformado em `knowledge_source` e `knowledge_chunk`, sem precisar gerar JSON manual.

## 8. Treinamento supervisionado

Endpoints principais:

```txt
GET  /api/v1/training/candidates
PUT  /api/v1/training/candidates/{candidate_id}
POST /api/v1/training/candidates/{candidate_id}/approve
POST /api/v1/training/candidates/{candidate_id}/reject
POST /api/v1/training/candidates/auto-approve
```

Ao aprovar um candidato, o backend:

1. Atualiza o status do candidato.
2. Monta um conteúdo de treinamento aprovado.
3. Cria uma fonte em `knowledge_sources`.
4. Quebra o conteúdo em chunks.
5. Gera embedding.
6. Salva os chunks.
7. Marca o candidato como `indexed`.

## 9. Autoaprovação

Endpoint:

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

O parâmetro pode ser aumentado conforme a base amadurecer.

## 10. Frontend

O frontend foi ajustado para experiência estilo ChatGPT:

- Input fixo na parte inferior.
- Mensagens acima.
- Sidebar limpa.
- Modal para arquivos indexados.
- Modal para fontes da resposta.
- Feedback por resposta.

## 11. Banco de dados

O Postgres usa volume persistente:

```yaml
volumes:
  - postgres_data:/var/lib/postgresql/data
```

Não use `docker compose down -v` se quiser preservar dados, feedbacks e treinamentos.

## 12. Comandos úteis

Subir tudo:

```bash
docker compose up -d
```

Rebuild apenas do backend:

```bash
docker compose up -d --build ai-api
```

Rebuild apenas do frontend:

```bash
docker compose up -d --build frontend
```

Ver logs do backend:

```bash
docker compose logs ai-api --tail=150
```

Testar Ollama:

```bash
curl http://localhost:11434/api/tags
```

Testar geração Ollama:

```bash
curl -X POST http://localhost:11434/api/generate ^
  -H "Content-Type: application/json" ^
  -d "{\"model\":\"llama3.2:1b\",\"prompt\":\"responda apenas ok\",\"stream\":false}"
```
