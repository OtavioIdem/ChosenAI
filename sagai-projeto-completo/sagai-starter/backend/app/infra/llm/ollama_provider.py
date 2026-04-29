from __future__ import annotations

import os

import httpx

from app.infra.llm.base import ChatMessage, RetrievedContext


class OllamaLLMProvider:
    """Provider local para Ollama.

    Versão validada para o cenário atual do SAGAI:
    - backend rodando em Docker;
    - Ollama rodando no host Windows;
    - endpoint /api/generate;
    - suporte a mensagens Pydantic ou dict;
    - suporte a contexto RAG;
    - fallback amigável para erro de timeout/modelo indisponível.
    """

    async def generate(
        self,
        messages: list[ChatMessage],
        contexts: list[RetrievedContext] | None = None,
    ) -> str:
        base_url = self._env("OLLAMA_BASE_URL", "LLM_BASE_URL", default="http://host.docker.internal:11434")
        model = self._env("OLLAMA_MODEL", "LLM_MODEL", default="llama3.2:1b")
        timeout_seconds = int(self._env("LLM_TIMEOUT_SECONDS", default="300"))

        prompt = self._build_prompt(messages=messages, contexts=contexts or [])

        try:
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                response = await client.post(
                    f"{base_url.rstrip('/')}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                    },
                )

                response.raise_for_status()
                data = response.json()

                content = data.get("response", "")
                if not content:
                    return "O modelo local respondeu vazio. Verifique o modelo configurado no Ollama."

                return content.strip()

        except httpx.ReadTimeout:
            return (
                "Não foi possível gerar uma resposta porque o modelo local demorou "
                "mais do que o tempo limite configurado. Tente novamente, aumente "
                "LLM_TIMEOUT_SECONDS ou utilize um modelo mais leve no Ollama."
            )

        except httpx.HTTPStatusError as error:
            status_code = error.response.status_code if error.response else "desconhecido"
            response_text = ""
            try:
                response_text = error.response.text[:500]
            except Exception:
                response_text = ""

            return (
                "Não foi possível consultar o modelo local. "
                f"Ollama retornou status {status_code}. "
                "Verifique se OLLAMA_MODEL está instalado, se OLLAMA_BASE_URL está correto "
                "e se o Ollama está rodando. "
                f"Detalhe: {response_text}"
            )

        except httpx.RequestError as error:
            return (
                "Não foi possível conectar ao Ollama. Verifique se o serviço está rodando "
                "em http://localhost:11434 e se o Docker consegue acessar "
                "http://host.docker.internal:11434. "
                f"Detalhe: {str(error)}"
            )

        except Exception as error:
            return f"Erro ao consultar o modelo local pelo Ollama: {str(error)}"

    def _build_prompt(self, messages: list[ChatMessage], contexts: list[RetrievedContext]) -> str:
        message_text = "\n\n".join(
            f"{self._get_message_value(message, 'role', 'user').upper()}: "
            f"{self._get_message_value(message, 'content', '')}"
            for message in messages
        )

        if not contexts:
            return message_text

        context_text = "\n\n---\n\n".join(self._format_context(context) for context in contexts)

        return (
            "CONTEXTO RAG RECUPERADO:\n"
            f"{context_text}\n\n"
            "INSTRUÇÕES E PERGUNTA:\n"
            f"{message_text}"
        )

    def _format_context(self, context: RetrievedContext) -> str:
        metadata = getattr(context, "metadata", {}) or {}
        source = metadata.get("file") or metadata.get("source") or getattr(context, "source_identifier", "")

        return (
            f"Título: {getattr(context, 'title', 'Sem título')}\n"
            f"Fonte: {source}\n"
            f"Identificador: {getattr(context, 'source_identifier', '')}\n"
            f"Trecho: {getattr(context, 'chunk_index', 0) + 1}\n"
            f"Score: {getattr(context, 'score', 0.0):.4f}\n"
            f"Conteúdo:\n{getattr(context, 'content', '')}"
        )

    def _get_message_value(self, message: ChatMessage | dict, field: str, default: str = "") -> str:
        if isinstance(message, dict):
            return str(message.get(field, default))
        return str(getattr(message, field, default))

    def _env(self, *names: str, default: str = "") -> str:
        for name in names:
            value = os.getenv(name)
            if value not in (None, ""):
                return value
        return default
