from __future__ import annotations

import httpx

from app.config.settings import get_settings
from app.infra.llm.base import ChatMessage, RetrievedContext


class OpenAICompatibleLLMProvider:
    async def generate(self, messages: list[ChatMessage], contexts: list[RetrievedContext]) -> str:
        settings = get_settings()
        headers = {"Content-Type": "application/json"}
        if settings.llm_api_key:
            headers["Authorization"] = f"Bearer {settings.llm_api_key}"

        payload = {
            "model": settings.llm_model,
            "messages": [message.model_dump() for message in messages],
            "temperature": 0.1,
        }

        async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
            response = await client.post(
                f"{settings.llm_base_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("Empty response from OpenAI-compatible provider")

        content = choices[0].get("message", {}).get("content")
        if not content:
            raise RuntimeError("Missing message content from OpenAI-compatible provider")
        return content.strip()
