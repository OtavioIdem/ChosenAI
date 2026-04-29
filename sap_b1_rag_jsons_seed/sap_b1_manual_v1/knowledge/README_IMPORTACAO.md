# Pacote RAG — Manual Canônico SAP Business One Usuário Final v1

Este pacote foi criado para resolver um problema comum em RAG: usar apenas chunks soltos pode fazer a IA perder contexto. A recomendação aqui é manter um **manual completo** como fonte principal e usar chunks menores como complemento.

## Arquivos

- `manual_operacional_sap_b1_usuario_final_v1.md`  
  Manual completo, legível por humanos, para revisão funcional.

- `manual_operacional_sap_b1_usuario_final_v1.sagai.json`  
  Mesmo manual em formato JSON compatível com o pipeline atual do SAGAI.

- `chunks_complementares_sap_b1_usuario_final_v1.json`  
  Registros por rotina, derivados do manual canônico.

- `mapa_intencoes_sap_b1_usuario_final_v1.json`  
  Regras de roteamento semântico para perguntas comuns.

- `perguntas_avaliacao_rag_sap_b1_usuario_final_v1.json`  
  Golden questions para testar se a IA recupera o assunto correto.

- `fontes_consultadas_sap_b1_usuario_final_v1.json`  
  Lista de fontes públicas/oficiais usadas como base.

## Como importar no SAGAI

Copie os arquivos JSON para:

```txt
backend/knowledge/json/sap_b1/canonical_user_manual/
```

Sugestão:

```txt
backend/knowledge/json/sap_b1/canonical_user_manual/manual_operacional_sap_b1_usuario_final_v1.sagai.json
backend/knowledge/json/sap_b1/canonical_user_manual/chunks_complementares_sap_b1_usuario_final_v1.json
backend/knowledge/json/sap_b1/canonical_user_manual/mapa_intencoes_sap_b1_usuario_final_v1.json
backend/knowledge/json/sap_b1/canonical_user_manual/perguntas_avaliacao_rag_sap_b1_usuario_final_v1.json
```

Depois execute a reindexação:

```bash
curl -X POST "http://localhost:8000/api/v1/knowledge/reindex" -H "X-Admin-Key: SUA_ADMIN_API_KEY"
```

## Estratégia recomendada

1. O manual canônico deve ser tratado como a fonte principal.
2. Os chunks devem complementar a busca, não substituir o manual.
3. Conteúdo fiscal brasileiro deve sempre exigir validação humana antes de virar resposta operacional definitiva.
4. Mantenha versionamento: `v1`, `v2`, `v3` etc.
5. Sempre que atualizar o manual, gere novos chunks derivados para manter consistência.

## Observação sobre o pipeline atual

O normalizador do SAGAI aceita JSON único ou lista de JSONs com campos como `title`, `module`, `category` e `content`. Este pacote respeita esse formato.

