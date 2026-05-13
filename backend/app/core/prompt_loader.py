from __future__ import annotations

from pathlib import Path

from app.config.settings import get_settings


DEFAULT_PROMPT = """\
Você é o SAGAI, um assistente especializado no MaxManager.

Regras obrigatórias:
1. Responda apenas com base no contexto documental recuperado.
2. Não invente funcionalidades, botões, menus, regras ou fluxos.
3. Se não houver base suficiente, diga claramente que não encontrou documentação suficiente.
4. Prefira respostas objetivas, didáticas e orientadas a operação.
5. Quando possível, organize em: resposta direta, passo a passo, observações e fonte.
6. Nunca execute ações. Você apenas orienta.
"""


def load_system_prompt() -> str:
    settings = get_settings()
    prompt_path: Path = settings.prompt_file

    if not prompt_path.exists():
        return DEFAULT_PROMPT

    content = prompt_path.read_text(encoding="utf-8").strip()
    return content or DEFAULT_PROMPT
