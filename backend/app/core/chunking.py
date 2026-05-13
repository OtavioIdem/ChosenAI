from __future__ import annotations

import re


def chunk_text(text: str, max_chunk_size: int, chunk_overlap: int) -> list[str]:
    normalized = re.sub(r"\r\n?", "\n", text).strip()
    if not normalized:
        return []

    if len(normalized) <= max_chunk_size:
        return [normalized]

    chunks: list[str] = []
    start = 0
    length = len(normalized)

    while start < length:
        end = min(start + max_chunk_size, length)
        chunk = normalized[start:end]

        if end < length:
            last_break = max(chunk.rfind("\n\n"), chunk.rfind(". "), chunk.rfind("; "), chunk.rfind(" "))
            if last_break > int(max_chunk_size * 0.6):
                end = start + last_break + 1
                chunk = normalized[start:end]

        chunk = chunk.strip()
        if chunk:
            chunks.append(chunk)

        if end >= length:
            break

        start = max(0, end - chunk_overlap)

    return chunks
