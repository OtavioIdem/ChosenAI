# Manual Operacional Canônico — SAP Business One para Usuário Final

**Versão:** v1.0  
**Data de geração:** 2026-04-29  
**Finalidade:** servir como documento-mãe para treinamento RAG de uma IA especializada em SAP Business One.  
**Uso recomendado:** manter este manual como fonte principal canônica e usar os JSONs de chunks complementares apenas como reforço de recuperação semântica.

> Este material é um resumo operacional estruturado a partir de documentação pública/oficial da SAP e deve ser validado pela equipe funcional antes de uso produtivo. Em localização Brasil, rotinas fiscais como Nota Fiscal, NF-e, impostos, CFOP, CST, retenções, SPED e transmissão fiscal exigem validação humana especializada.

---

## 1. Modelo recomendado de conhecimento

Para este projeto, a IA deve trabalhar com três camadas:

1. **Documento canônico completo**
   - Manual em Markdown e JSON único.
   - Serve como fonte principal.
   - Traz contexto, termos, cautelas e passo a passo completo.

2. **Chunks complementares**
   - Registros menores por rotina.
   - Melhoram busca por perguntas curtas como "como dar baixa?" ou "onde aprovo pedido?".
   - Devem apontar para o documento canônico.

3. **Perguntas de avaliação**
   - Conjunto de perguntas esperadas para testar recuperação.
   - Usadas para medir se a IA consulta a fonte correta.

---

## 2. Política de resposta da IA

Quando responder sobre SAP Business One, a IA deve:

- Responder em português brasileiro.
- Dizer o módulo relacionado.
- Entregar passo a passo prático.
- Separar baixa financeira, baixa de estoque e aprovação.
- Informar pré-requisitos.
- Alertar quando houver impacto fiscal, contábil, financeiro ou de estoque.
- Não inventar nomes de telas quando a fonte não sustentar.
- Em Brasil, tratar Nota Fiscal como tema fiscal/localizado, exigindo validação de parametrização.

---

## 3. Fontes documentais utilizadas

- **SAP Business One — Web Client User Guide** — autoridade: `official_sap`. Uso: Base operacional para Web Client: documentos de vendas, compras, pagamentos, aprovações, drafts e movimentações. URL: https://help.sap.com/doc/ceedc4fe720a4fc19a8e1fa75bdf02f7/10.0_FP_2305/en-US/ab9cf61542fb4359ae1ee7a972f920d5.pdf
- **SAP Business One Administrator's Guide 10.0 SP 2505** — autoridade: `official_sap`. Uso: Base administrativa para instalação, segurança, usuários, autenticação e administração do ambiente. URL: https://help.sap.com/doc/f971ebb2d51940f597f9e746d5aa019b/10.0_SP_2505/en-US/9a2e1e4e14b3486099852acf7a8bcd84.pdf
- **SAP Learning — Managing Users and User Groups** — autoridade: `official_sap_learning`. Uso: Conceitos sobre usuário, licença, grupos, superusuário e autorizações. URL: https://learning.sap.com/courses/implementing-sap-business-one/managing-users-and-user-groups
- **SAP Learning — Defining General Authorizations** — autoridade: `official_sap_learning`. Uso: Conceitos sobre autorização geral, grupos de autorização e cópia de permissões. URL: https://learning.sap.com/courses/implementing-sap-business-one/defining-general-authorizations
- **SAP Help Portal — Nota Fiscal: Brazil** — autoridade: `official_sap`. Uso: Contexto de localização Brasil e conceito de Nota Fiscal em transações de entrada e saída. URL: https://help.sap.com/docs/SAP_BUSINESS_ONE/4228b3b6daa64784b4eed1ff2d9a350e/c87d5602d5ba4850864cba8e5a3e571e.html

---

## 4. Rotinas operacionais

### 4.1. Criar usuário no SAP Business One

**ID:** `sap_b1_user_create_desktop`  
**Módulo:** Administração  
**Categoria:** usuario_e_autorizacao  
**Confiança:** high  
**Requer validação humana:** não  

#### Objetivo
Orientar a criação ou manutenção básica de usuários no SAP Business One.

#### Pré-requisitos
- Acesso de administrador ou superusuário.
- Licença disponível para o usuário.
- Definição prévia do perfil funcional do usuário.
- Quando houver IAM/IDP configurado, validar vínculo entre usuário SAP B1 e identidade externa.

#### Caminho de acesso
- Client desktop: Administration > Setup > General > Users

#### Passo a passo
1. Acesse o menu Administration > Setup > General > Users.
2. Crie um novo registro de usuário ou localize um usuário existente.
3. Informe o código do usuário, nome, e dados básicos exigidos pelo ambiente.
4. Associe licença conforme o tipo de acesso necessário.
5. Defina se o usuário será superusuário apenas quando houver necessidade real de acesso completo.
6. Configure grupo de usuários, filial/branch, departamento ou vínculo organizacional quando aplicável.
7. Salve o cadastro.
8. Depois de salvar, revise autorizações gerais, propriedade de dados e acessos de UI conforme o perfil.

#### Resultado esperado
Usuário criado e apto a receber permissões, licença e configurações complementares.

#### Observações importantes
- Não conceda superuser para usuários operacionais sem necessidade.
- Superusuário possui acesso amplo e normalmente exige licença profissional.
- A criação do usuário não garante acesso a todos os módulos; autorizações precisam ser revisadas.
- Em ambientes com autenticação integrada ou OpenID Connect, o usuário pode precisar de vínculo com provedor de identidade.

#### Palavras-chave para recuperação
criar usuário, user code, usuário, licença, superuser, autorização, Administration Setup General Users

#### Estilo de resposta recomendado
Responder em passo a passo. Se o usuário perguntar apenas 'como criar usuário', explicar menu, campos básicos, licença e alerta de autorização.

---

### 4.2. Configurar autorizações gerais para usuários

**ID:** `sap_b1_authorizations_basic`  
**Módulo:** Administração  
**Categoria:** usuario_e_autorizacao  
**Confiança:** high  
**Requer validação humana:** não  

#### Objetivo
Orientar a concessão e revisão de autorizações no SAP Business One.

#### Pré-requisitos
- Usuário previamente criado.
- Perfil de acesso definido por função.
- Acesso de administrador/superusuário.

#### Caminho de acesso
- Client desktop: Administration > System Initialization > Authorizations > General Authorizations

#### Passo a passo
1. Acesse a janela de General Authorizations.
2. Selecione o usuário ou grupo de usuários.
3. Navegue pela árvore de módulos e funcionalidades.
4. Defina autorização como plena, somente leitura, sem autorização ou outro nível disponível conforme a função.
5. Use grupos de usuários para padronizar permissões por perfil.
6. Quando aplicável, copie autorizações de um usuário modelo para outro usuário similar.
7. Salve as alterações.
8. Solicite que o usuário teste o acesso em uma rotina real controlada.

#### Resultado esperado
Usuário passa a ter acesso coerente com seu perfil operacional.

#### Observações importantes
- Autorização geral controla acesso, mas pode existir controle adicional por filial, propriedade de dados, licença, layout de UI ou add-ons.
- Alterações de permissão devem ser auditadas.
- Para usuários superuser, as autorizações não são normalmente ajustadas item a item.

#### Palavras-chave para recuperação
autorizações, permissões, general authorizations, grupo de usuários, copiar autorização, superuser

#### Estilo de resposta recomendado
Diferenciar criação de usuário de permissão. Para erro de acesso negado, orientar verificar licença, autorização geral, grupo e propriedade de dados.

---

### 4.3. Criar nota/fatura de saída no SAP Business One

**ID:** `sap_b1_ar_invoice_create`  
**Módulo:** Vendas - Contas a Receber  
**Categoria:** documento_venda  
**Confiança:** medium  
**Requer validação humana:** sim  

#### Objetivo
Orientar a criação de documento de venda do tipo A/R Invoice. Em localização Brasil, validar regras fiscais, NF-e e add-ons.

#### Pré-requisitos
- Parceiro de negócio cliente cadastrado.
- Itens ou serviços cadastrados.
- Condição de pagamento, depósito, impostos e dados fiscais revisados.
- Autorização para criar documento de venda.
- Quando houver localização Brasil, parametrização fiscal validada.

#### Caminho de acesso
- Web Client: app/tile relacionado a A/R Invoices.
- Client desktop: Sales - A/R > A/R Invoice.

#### Passo a passo
1. Acesse a rotina de A/R Invoice ou documento fiscal de saída equivalente no ambiente.
2. Clique em Create ou adicione novo documento.
3. Selecione o cliente.
4. Informe data de lançamento, data de vencimento e data do documento conforme política da empresa.
5. Inclua itens ou serviços nas linhas.
6. Confirme quantidade, preço, depósito, impostos, centro de custo e demais dimensões quando aplicável.
7. Revise totais, condição de pagamento e observações.
8. Salve/adiciona o documento.
9. Se o processo exigir aprovação, acompanhe o draft até aprovação.
10. No Brasil, siga o fluxo fiscal/localização para geração/transmissão da NF-e quando aplicável.

#### Resultado esperado
Documento de saída criado, afetando contas a receber, estoque e contabilidade conforme configuração.

#### Observações importantes
- A/R Invoice em SAP B1 é documento de venda/contas a receber; no Brasil pode estar relacionado à Nota Fiscal de saída, mas a emissão fiscal depende da localização e configuração.
- Não orientar XML, CFOP, CST, impostos ou transmissão sem fonte fiscal específica e validação humana.
- Documento pode ser criado a partir de pedido ou entrega, dependendo do processo da empresa.

#### Palavras-chave para recuperação
nota fiscal de saída, fatura de saída, A/R Invoice, invoice, vendas, contas a receber, NF-e

#### Estilo de resposta recomendado
Usar o termo A/R Invoice e explicar a equivalência com nota/fatura de saída com ressalva fiscal brasileira.

---

### 4.4. Criar nota/fatura de entrada no SAP Business One

**ID:** `sap_b1_ap_invoice_create`  
**Módulo:** Compras - Contas a Pagar  
**Categoria:** documento_compra  
**Confiança:** medium  
**Requer validação humana:** sim  

#### Objetivo
Orientar a criação de documento de compra do tipo A/P Invoice. Em localização Brasil, validar regras fiscais e escrituração.

#### Pré-requisitos
- Fornecedor cadastrado como parceiro de negócio.
- Item/serviço cadastrado.
- Pedido de compra ou recebimento de mercadoria, quando o processo exigir.
- Condição de pagamento, impostos e dados fiscais revisados.
- Autorização para criar documentos de compra.

#### Caminho de acesso
- Web Client: app/tile relacionado a A/P Invoices.
- Client desktop: Purchasing - A/P > A/P Invoice.

#### Passo a passo
1. Acesse a rotina de A/P Invoice ou documento de entrada equivalente.
2. Clique em Create ou adicione novo documento.
3. Selecione o fornecedor.
4. Informe datas e número de referência do documento recebido.
5. Inclua itens ou serviços, ou copie de documento anterior como pedido/recebimento, se aplicável.
6. Revise quantidade, preço, impostos, depósito e centro de custo.
7. Confira vencimento e condição de pagamento.
8. Salve/adiciona o documento.
9. Se houver aprovação, acompanhe o draft até liberação.
10. No Brasil, valide escrituração, dados fiscais, CFOP, impostos e integração fiscal conforme parametrização local.

#### Resultado esperado
Documento de entrada criado, afetando contas a pagar, estoque e contabilidade conforme configuração.

#### Observações importantes
- A/P Invoice representa documento de compra/contas a pagar.
- No Brasil, nota fiscal de entrada envolve localização fiscal e deve ser validada com equipe fiscal/SAP responsável.
- Quando a entrada vem de mercadoria, pode haver relação com Goods Receipt PO.

#### Palavras-chave para recuperação
nota fiscal de entrada, fatura de entrada, A/P Invoice, compras, contas a pagar, entrada fiscal

#### Estilo de resposta recomendado
Responder com passo a passo e separar claramente compra operacional de regra fiscal brasileira.

---

### 4.5. Dar baixa financeira em contas a receber por recebimento

**ID:** `sap_b1_incoming_payment`  
**Módulo:** Bancos e Pagamentos  
**Categoria:** baixa_financeira  
**Confiança:** high  
**Requer validação humana:** não  

#### Objetivo
Orientar a baixa financeira de documento de venda/contas a receber por meio de pagamento recebido.

#### Pré-requisitos
- Documento de contas a receber lançado.
- Meio de pagamento definido.
- Conta bancária/caixa configurada.
- Autorização para pagamentos recebidos.

#### Caminho de acesso
- Web Client: criar pagamento a partir do cliente, da lista de A/R Invoices ou botão Pay na fatura.
- Client desktop: Banking > Incoming Payments > Incoming Payments.

#### Passo a passo
1. Acesse a rotina de Incoming Payment ou pagamento recebido.
2. Selecione o cliente.
3. Localize os documentos em aberto.
4. Marque a fatura/lançamento que será baixado.
5. Informe valor recebido, data e meio de pagamento.
6. Confirme conta bancária/caixa e demais informações financeiras.
7. Revise diferença, desconto, juros ou arredondamento se existir.
8. Adicione/salve o pagamento.
9. Verifique se o documento ficou liquidado ou parcialmente liquidado.

#### Resultado esperado
Título de contas a receber baixado total ou parcialmente, com lançamento financeiro correspondente.

#### Observações importantes
- Baixa financeira é diferente de baixa de estoque.
- Se houver diferença de valor, pode existir tratamento específico para desconto, juros, taxa bancária ou pagamento parcial.
- Conciliação bancária pode ser etapa posterior.

#### Palavras-chave para recuperação
baixa, recebimento, incoming payment, contas a receber, A/R invoice, pagamento recebido

#### Estilo de resposta recomendado
Quando o usuário disser 'dar baixa', perguntar ou inferir se é baixa financeira, estoque ou aprovação. Se for financeiro de cliente, orientar Incoming Payment.

---

### 4.6. Dar baixa financeira em contas a pagar por pagamento efetuado

**ID:** `sap_b1_outgoing_payment`  
**Módulo:** Bancos e Pagamentos  
**Categoria:** baixa_financeira  
**Confiança:** high  
**Requer validação humana:** não  

#### Objetivo
Orientar a baixa financeira de documento de compra/contas a pagar por meio de pagamento efetuado.

#### Pré-requisitos
- Documento de contas a pagar lançado.
- Meio de pagamento e conta bancária configurados.
- Autorização para outgoing payments.

#### Caminho de acesso
- Web Client: criar pagamento a partir do fornecedor, da lista de A/P Invoices ou botão Pay na fatura.
- Client desktop: Banking > Outgoing Payments > Outgoing Payments.

#### Passo a passo
1. Acesse a rotina de Outgoing Payment ou pagamento efetuado.
2. Selecione o fornecedor.
3. Localize as faturas ou lançamentos em aberto.
4. Marque o documento que será pago.
5. Informe valor, data, meio de pagamento e conta.
6. Revise retenções, descontos ou diferenças quando aplicável.
7. Adicione/salve o pagamento.
8. Confira se o contas a pagar ficou liquidado ou parcialmente liquidado.

#### Resultado esperado
Título de contas a pagar baixado total ou parcialmente, com lançamento financeiro correspondente.

#### Observações importantes
- Pagamentos podem exigir aprovação, dependendo da configuração.
- No Brasil, retenções e impostos podem afetar o valor líquido do pagamento.
- Conciliação bancária pode ser etapa posterior.

#### Palavras-chave para recuperação
baixa, pagamento, outgoing payment, contas a pagar, A/P invoice, pagamento efetuado

#### Estilo de resposta recomendado
Se a dúvida mencionar fornecedor ou contas a pagar, orientar Outgoing Payment.

---

### 4.7. Dar baixa de estoque por saída de mercadoria

**ID:** `sap_b1_goods_issue`  
**Módulo:** Estoque  
**Categoria:** movimentacao_estoque  
**Confiança:** high  
**Requer validação humana:** não  

#### Objetivo
Orientar a saída manual de mercadorias do estoque quando o processo não estiver vinculado a documento de venda/produção.

#### Pré-requisitos
- Item cadastrado como item de estoque.
- Saldo disponível no depósito.
- Depósito correto identificado.
- Autorização para Goods Issue.

#### Caminho de acesso
- Web Client: app/tile relacionado a Goods Issues.
- Client desktop: Inventory > Inventory Transactions > Goods Issue.

#### Passo a passo
1. Acesse Goods Issue ou saída de mercadoria.
2. Crie um novo documento.
3. Informe data e observação/motivo da saída.
4. Inclua o item.
5. Informe quantidade e depósito.
6. Preencha centro de custo, projeto ou dimensões quando aplicável.
7. Revise o impacto de estoque e contabilidade.
8. Adicione/salve o documento.
9. Confirme se o saldo foi reduzido no depósito correto.

#### Resultado esperado
Saldo de estoque reduzido conforme documento de saída de mercadoria.

#### Observações importantes
- Goods Issue não é baixa financeira.
- Usar apenas quando o processo da empresa permitir saída manual.
- Saídas vinculadas a vendas, produção ou transferência podem usar documentos próprios.

#### Palavras-chave para recuperação
baixa de estoque, goods issue, saída de mercadoria, almoxarifado, estoque

#### Estilo de resposta recomendado
Para pergunta 'como dou baixa no sistema?', diferenciar baixa de estoque, baixa financeira e baixa/aprovação de documento.

---

### 4.8. Acessar aprovações de pedidos ou documentos

**ID:** `sap_b1_approval_decisions`  
**Módulo:** Aprovações  
**Categoria:** workflow_aprovacao  
**Confiança:** high  
**Requer validação humana:** não  

#### Objetivo
Orientar o aprovador a acessar e decidir solicitações pendentes de aprovação.

#### Pré-requisitos
- Processo de aprovação configurado.
- Usuário definido como aprovador/autorizador.
- Documento criado ou atualizado por usuário que disparou aprovação.
- Autorização para acessar Approval Decisions.

#### Caminho de acesso
- Web Client: tile Approval Decisions / Manage Approval Decisions.
- Client desktop: caminhos podem variar conforme versão/configuração de Approval Procedures.

#### Passo a passo
1. Acesse o Web Client.
2. Abra o tile Approval Decisions.
3. Na lista Manage Approval Decisions, filtre solicitações pendentes se necessário.
4. Abra o draft/documento pendente.
5. Revise dados principais: parceiro, valores, itens, impostos, datas e observações.
6. Escolha aprovar ou rejeitar.
7. Informe comentário se o processo exigir.
8. Confirme a decisão.
9. O originador deve acompanhar o status para finalizar ou ajustar o documento.

#### Resultado esperado
Solicitação aprovada ou rejeitada; o documento segue o fluxo definido pela empresa.

#### Observações importantes
- O processo de aprovação precisa estar configurado previamente.
- A aprovação normalmente trabalha com draft antes do documento final.
- Rejeição pode exigir correção e reenvio pelo originador.

#### Palavras-chave para recuperação
aprovação, approval decisions, pedidos pendentes, aprovar pedido, reject, approve, draft

#### Estilo de resposta recomendado
Responder com foco em Approval Decisions e explicar a diferença entre originador e aprovador.

---

### 4.9. Entender e acompanhar drafts gerados por aprovação

**ID:** `sap_b1_document_drafts`  
**Módulo:** Aprovações  
**Categoria:** workflow_aprovacao  
**Confiança:** high  
**Requer validação humana:** não  

#### Objetivo
Explicar o comportamento de rascunhos quando um documento exige aprovação.

#### Pré-requisitos
- Procedimento de aprovação configurado.
- Usuário cria/atualiza documento que atende condição de aprovação.

#### Caminho de acesso
- Web Client: lista de drafts ou fluxo de Approval Decisions, conforme perfil.

#### Passo a passo
1. Ao criar ou atualizar um documento que exige aprovação, o sistema informa que aprovação é necessária.
2. O documento fica como draft/rascunho.
3. O aprovador acessa Approval Decisions e analisa o draft.
4. Se aprovado, o originador pode seguir o fluxo para concluir o documento, conforme configuração.
5. Se rejeitado, o originador deve ajustar ou cancelar o rascunho conforme orientação interna.

#### Resultado esperado
Usuário entende por que o documento não foi lançado imediatamente e como acompanhar a aprovação.

#### Observações importantes
- Draft não é necessariamente documento final lançado.
- A regra de aprovação pode depender de valor, desconto, parceiro de negócio, documento, usuário ou outra condição configurada.

#### Palavras-chave para recuperação
draft, rascunho, aprovação, documento pendente, originador, autorizador

#### Estilo de resposta recomendado
Usar quando o usuário reclamar que 'o pedido ficou pendente' ou 'não consigo finalizar porque pediu aprovação'.

---

### 4.10. Cadastrar parceiro de negócio básico

**ID:** `sap_b1_bp_create_basic`  
**Módulo:** Parceiros de Negócio  
**Categoria:** cadastro  
**Confiança:** medium  
**Requer validação humana:** sim  

#### Objetivo
Orientar cadastro básico de cliente ou fornecedor antes de documentos de venda/compra.

#### Pré-requisitos
- Definição se o parceiro será cliente, fornecedor ou lead.
- Dados cadastrais e fiscais disponíveis.
- Grupo, condição de pagamento e moeda definidos.
- No Brasil, dados fiscais e endereço devem ser validados.

#### Caminho de acesso
- Web Client: app/tile Business Partners.
- Client desktop: Business Partners > Business Partner Master Data.

#### Passo a passo
1. Acesse Business Partner Master Data ou app Business Partners.
2. Crie um novo parceiro.
3. Selecione tipo: cliente, fornecedor ou lead.
4. Informe código, nome e grupo.
5. Preencha endereço, contatos e dados de pagamento.
6. Configure condições comerciais, moeda, limite de crédito e vendedor/comprador quando aplicável.
7. Revise dados fiscais e de localização.
8. Salve o cadastro.
9. Utilize o parceiro em documento de venda ou compra.

#### Resultado esperado
Parceiro de negócio disponível para uso em documentos e processos.

#### Observações importantes
- Dados fiscais brasileiros exigem validação específica.
- Erro no cadastro pode impactar documento fiscal, pagamento, cobrança e relatórios.

#### Palavras-chave para recuperação
cliente, fornecedor, parceiro de negócio, business partner, BP, cadastro

#### Estilo de resposta recomendado
Fornecer passo a passo básico e alertar sobre dados fiscais quando Brasil.

---

### 4.11. Navegar no SAP Business One Web Client

**ID:** `sap_b1_navigation_web_client`  
**Módulo:** Web Client  
**Categoria:** navegacao  
**Confiança:** high  
**Requer validação humana:** não  

#### Objetivo
Ensinar conceitos básicos de navegação no Web Client para encontrar, filtrar, criar e editar registros.

#### Pré-requisitos
- Usuário com acesso ao Web Client.
- Permissões para os apps relevantes.

#### Caminho de acesso
- Página inicial do Web Client com tiles/apps.

#### Passo a passo
1. Acesse o Web Client com seu usuário.
2. Na página inicial, localize o tile/app do processo desejado.
3. Abra a list view para pesquisar e filtrar registros.
4. Use filtros, ordenação e busca para localizar documentos.
5. Abra um registro para acessar a detailed view.
6. Quando autorizado, use Create para novo documento ou Edit para alterar registro permitido.
7. Use ações de documento como Cancel, Close, Copy To/Copy From ou Pay quando disponíveis e permitidas.

#### Resultado esperado
Usuário consegue navegar entre lista, detalhe e criação de registros no Web Client.

#### Observações importantes
- Nem todos os recursos do client desktop existem no Web Client.
- Ações visíveis dependem de autorização, status do documento e versão.

#### Palavras-chave para recuperação
web client, tile, list view, detailed view, create, filter, visualizar, editar

#### Estilo de resposta recomendado
Usar para perguntas genéricas como 'onde eu acesso isso no SAP B1 Web'.

---

## 5. Orientação para perguntas ambíguas

### Pergunta: "Como faço baixa no SAP?"
A IA não deve assumir automaticamente o tipo de baixa. Ela deve diferenciar:

- **Baixa financeira de cliente:** Incoming Payment / Pagamento recebido.
- **Baixa financeira de fornecedor:** Outgoing Payment / Pagamento efetuado.
- **Baixa de estoque:** Goods Issue / Saída de mercadoria.
- **Baixa/aprovação de documento:** fluxo de Approval Decisions ou draft.

Resposta recomendada:
"Você quer baixa financeira, baixa de estoque ou aprovação/encerramento de documento? Se for baixa financeira de cliente, use Incoming Payment; se for fornecedor, Outgoing Payment; se for estoque, Goods Issue."

### Pergunta: "Como faço nota fiscal de saída?"
A IA deve responder:
- Processo base: A/R Invoice ou documento de venda.
- No Brasil: NF-e/Nota Fiscal depende de localização fiscal, impostos, CFOP, CST, série, modelo, parceiro, item, add-ons e integração fiscal.
- Encaminhar para validação fiscal se a pergunta envolver XML, transmissão, rejeição ou imposto.

### Pergunta: "Como faço nota fiscal de entrada?"
A IA deve responder:
- Processo base: A/P Invoice ou documento de compra.
- No Brasil: entrada fiscal depende de regras de localização, documento recebido, impostos e escrituração.

### Pergunta: "Como aprovo pedido?"
A IA deve responder:
- Acessar Approval Decisions no Web Client quando o usuário for aprovador.
- Abrir solicitação pendente, revisar e aprovar/rejeitar.
- Se não aparecer, verificar se usuário é aprovador, se existe procedimento de aprovação e se há autorização.

---

## 6. Critérios de confiança

- **Alta:** rotinas gerais documentadas oficialmente e sem dependência fiscal local.
- **Média:** rotina operacional que varia por parametrização, versão ou localização.
- **Baixa:** perguntas sobre regra fiscal brasileira, add-ons específicos, customizações, SQL, integrações ou mensagens de erro sem código/fonte.

---

## 7. Como este manual deve ser usado no RAG

1. Indexar o arquivo JSON canônico completo.
2. Indexar os chunks complementares derivados.
3. Na resposta, preferir o manual canônico quando a pergunta exigir processo completo.
4. Usar chunks para localizar rapidamente o assunto.
5. Se a resposta depender de imposto, XML, localização ou customização, sinalizar necessidade de validação humana.

