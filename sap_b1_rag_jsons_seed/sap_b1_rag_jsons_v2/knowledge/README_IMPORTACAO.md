# SAP Business One RAG JSONs Expanded v2

Pacote ampliado de conhecimento seed para IA especializada em SAP Business One.

## Conteúdo

- Total de arquivos JSON: 16
- Total de registros/chunks: 142
- Idioma dos conteúdos: pt-BR
- Versão base: SAP Business One 10.0
- Pasta recomendada no projeto: `backend/knowledge/json/sap_b1/`

## Como importar

1. Extraia este pacote.
2. Copie a pasta `sap_b1_rag_jsons_expanded_v2` ou suas subpastas para:
   `backend/knowledge/json/sap_b1/`
3. Execute a reindexação:
   `POST /api/v1/knowledge/reindex`

## Política de uso

Este pacote é um seed de curadoria para RAG. Ele não substitui documentação oficial, consultoria SAP, contador ou consultor fiscal.

- Fontes SAP oficiais: podem entrar com confiança alta quando descrevem comportamento do SAP Business One.
- Fontes governamentais: confiança alta para regra fiscal externa, mas não para afirmar configuração SAP.
- Fiscal Brasil: manter `requires_human_validation = true` quando a resposta puder impactar operação, imposto, XML, SPED ou documentos fiscais.
- Integrações: nunca sugerir alteração direta no banco de dados para corrigir documentos ou transações.
- Add-ons/customizações: tratar como comportamento dependente do cliente até haver documentação interna.

## Estrutura

- `00_source_governance/sap_b1_source_governance.json`: 6 registros
- `01_core_overview/sap_b1_core_overview.json`: 6 registros
- `02_master_data/sap_b1_master_data.json`: 6 registros
- `03_financials/sap_b1_financials.json`: 8 registros
- `04_banking_reconciliation/sap_b1_banking_reconciliation.json`: 6 registros
- `05_sales_crm_ar/sap_b1_sales_crm_ar.json`: 8 registros
- `06_purchasing_ap/sap_b1_purchasing_ap.json`: 6 registros
- `07_inventory_warehouse/sap_b1_inventory_warehouse.json`: 8 registros
- `08_production_bom_mrp/sap_b1_production_bom_mrp.json`: 10 registros
- `09_service_projects/sap_b1_service_projects.json`: 10 registros
- `10_reporting_web_client_mobile/sap_b1_reporting_web_client_mobile.json`: 8 registros
- `11_technical_service_layer_api/sap_b1_service_layer_api.json`: 14 registros
- `12_technical_b1if_di_api_extensions/sap_b1_b1if_di_api_extensions.json`: 10 registros
- `13_localization_brazil_fiscal/sap_b1_localization_brazil_fiscal.json`: 12 registros
- `14_release_version_governance/sap_b1_release_version_governance.json`: 6 registros
- `15_intent_router_and_eval/sap_b1_intent_router_and_eval.json`: 18 registros

## Campos principais

Cada registro contém:

- `title`
- `module`
- `category`
- `keywords`
- `content`
- `source`
- `source_type`
- `source_authority`
- `confidence`
- `requires_human_validation`
- `sap_version`
- `questions`
- `answer_guidelines`
- `negative_rules`

## Sugestão de validação

Após reindexar, teste as golden questions do arquivo:
`15_intent_router_and_eval/sap_b1_intent_router_and_eval.json`

