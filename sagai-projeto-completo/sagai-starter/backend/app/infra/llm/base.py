from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: str


class RetrievedContext(BaseModel):
    title: str
    source_identifier: str
    chunk_index: int
    content: str
    score: float
    metadata: dict


class LLMProvider(Protocol):
    async def generate(self, messages: list[ChatMessage], contexts: list[RetrievedContext]) -> str:
        ...
