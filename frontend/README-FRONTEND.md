# SAGAI Frontend — UI estilo chat

Este pacote substitui o frontend atual por uma interface mais próxima de um chat moderno:

- caixa de texto fixa na parte inferior;
- mensagens em formato de conversa;
- resposta exibida logo acima do input;
- sidebar limpa com contadores de fontes/trechos;
- botão para abrir modal com todos os arquivos indexados;
- modal de fontes por resposta;
- botões de feedback por resposta;
- estado de carregamento com animação;
- sugestões iniciais de perguntas.

## Como aplicar

Copie/substitua a pasta `frontend` do seu projeto pela pasta deste pacote.

Depois rode na raiz do projeto:

```bash
docker compose down
docker compose up --build
```

## Observação

A UI depende dos endpoints já existentes:

- `GET /api/v1/knowledge/stats`
- `POST /api/v1/chat/ask`
- `POST /api/v1/feedback`

