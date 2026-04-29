# SAP B1 End User Operations RAG v3

Pacote de JSONs para treinar uma IA especializada em SAP Business One a responder perguntas de usuário final.

## Conteúdo

- Administração de usuários e autorizações
- Nota/fatura de saída: A/R Invoice
- Nota/fatura de entrada: A/P Invoice
- Baixa financeira por pagamentos
- Baixa de estoque por Goods Issue
- Aprovações de documentos no Web Client
- Roteamento de intenção para perguntas ambíguas

## Importação sugerida

Copiar a pasta para:

```text
backend/knowledge/json/sap_b1/end_user_operations/
```

Depois executar:

```http
POST /api/v1/knowledge/reindex
```

## Observações de curadoria

- Os registros foram escritos como resumos estruturados para RAG, não como reprodução integral da documentação SAP.
- Para Brasil, fluxos de NF-e, NFS-e, SPED, impostos e transmissão fiscal precisam de validação humana.
- O termo "baixa" pode significar baixa financeira ou baixa de estoque. O roteador incluído ajuda a classificar a intenção.

## Registros

Total: 14
