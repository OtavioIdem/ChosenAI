from __future__ import annotations

from app.infra.llm.base import ChatMessage, RetrievedContext


class MockLLMProvider:
    async def generate(self, messages: list[ChatMessage], contexts: list[RetrievedContext]) -> str:
        question = next((message.content for message in reversed(messages) if message.role == "user"), "")
        if not contexts:
            return (
                "Não encontrei base documental suficiente para responder com segurança. "
                "Revise a documentação disponível ou complemente a base inicial."
            )

        bullets = []
        for item in contexts[:4]:
            bullets.append(
                f"- Fonte: {item.title} | trecho {item.chunk_index + 1} | relevância: {item.score:.2f}\n"
                f"  {item.content[:360].strip()}"
            )

        return (
            "Resposta baseada na documentação recuperada.\n\n"
            f"Pergunta analisada: {question.strip()}\n\n"
            "Trechos mais relevantes:\n"
            f"{chr(10).join(bullets)}\n\n"
            "Observação: este é o modo mock/determinístico. Ao conectar um provedor LLM real, "
            "o SAGAI passará a sintetizar esses trechos em uma resposta mais natural."
        )
