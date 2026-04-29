# SAP Business One — pacote inicial de JSONs para RAG

Este pacote foi criado para testar a capacidade do SAGAI de trabalhar com um domínio diferente do MaxManager usando a mesma arquitetura de RAG.

## Conteúdo

- JSONs separados por módulos em `backend/knowledge/json/sap_b1/`
- Manifesto em `sap_b1_training_manifest.json`
- Total de arquivos JSON de módulo: 16
- Total de registros/chunks: 36

## Como importar no projeto

1. Copie a pasta `backend/knowledge/json/sap_b1` para a mesma pasta no projeto SAGAI.
2. Suba backend e banco normalmente.
3. Execute a reindexação geral:

```http
POST /api/v1/knowledge/reindex
```

## Observações de curadoria

- O conteúdo é um seed resumido/parafraseado, não uma cópia da documentação SAP.
- Cada chunk inclui fonte, palavras-chave, exemplos de pergunta, dependências e nível de confiança.
- Para produção real, validar cada módulo com consultor SAP B1 e, principalmente, revisar conteúdo fiscal/localização Brasil.
- Perguntas que exigem campo específico, procedimento exato de tela ou regra fiscal devem ser tratadas como lacuna até haver documentação detalhada.

## Módulos cobertos

- sap_b1_00_visao_geral.sagai.json
- sap_b1_01_administracao_configuracao.sagai.json
- sap_b1_02_cadastros_dados_mestres.sagai.json
- sap_b1_03_financeiro_contabilidade.sagai.json
- sap_b1_04_bancos_pagamentos_reconciliacao.sagai.json
- sap_b1_05_vendas_crm_ar.sagai.json
- sap_b1_06_compras_ap.sagai.json
- sap_b1_07_estoque_almoxarifado.sagai.json
- sap_b1_08_producao_bom.sagai.json
- sap_b1_09_mrp_planejamento.sagai.json
- sap_b1_10_servicos_pos_venda.sagai.json
- sap_b1_11_projetos.sagai.json
- sap_b1_12_bi_relatorios_analytics.sagai.json
- sap_b1_13_web_mobile_extensibilidade.sagai.json
- sap_b1_14_fiscal_localizacao_brasil.sagai.json
- sap_b1_99_intencoes_perguntas_frequentes.sagai.json
