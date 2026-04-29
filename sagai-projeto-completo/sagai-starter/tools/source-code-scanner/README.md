# SAGAI Source Code Scanner

Ferramenta opcional para varrer código-fonte e gerar um JSON técnico para o SAGAI.

Uso:

1. Copie o código do sistema para `source/`.
2. Rode:

```bash
docker compose up --build
```

3. O resultado será gerado em:

```txt
output/source_code_knowledge.json
```

4. Para usar no SAGAI, copie para:

```txt
backend/knowledge/json/generated/source_code_knowledge.json
```

5. Reindexe a base.
