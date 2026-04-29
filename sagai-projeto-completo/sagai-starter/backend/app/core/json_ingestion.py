from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def extract_text(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    if isinstance(value, (int, float, bool)):
        return str(value)

    if isinstance(value, list):
        parts = [extract_text(item) for item in value]
        return "\n".join(part for part in parts if part)

    if isinstance(value, dict):
        parts: list[str] = []
        for key, inner_value in value.items():
            text = extract_text(inner_value)
            if text:
                parts.append(f"{key}: {text}")
        return "\n".join(parts)

    return ""


def normalize_json_file(file_path: Path, root_dir: Path) -> list[dict[str, Any]]:
    raw = json.loads(file_path.read_text(encoding="utf-8"))
    records = raw if isinstance(raw, list) else [raw]

    relative_path = file_path.relative_to(root_dir).as_posix()
    normalized: list[dict[str, Any]] = []

    for index, record in enumerate(records):
        if isinstance(record, dict):
            title = (
                record.get("title")
                or record.get("name")
                or record.get("question")
                or record.get("operation")
                or file_path.stem
            )
            category = record.get("category") or record.get("module") or "General"
            content = (
                record.get("content")
                or record.get("text")
                or record.get("body")
                or record.get("answer")
                or extract_text(record)
            )
            metadata = {
                "category": category,
                "module": record.get("module"),
                "file": relative_path,
                "record_index": index,
            }
        else:
            title = f"{file_path.stem} #{index + 1}"
            category = "General"
            content = extract_text(record)
            metadata = {
                "category": category,
                "file": relative_path,
                "record_index": index,
            }

        normalized.append(
            {
                "source_identifier": f"{relative_path}::{index}",
                "title": str(title).strip(),
                "category": str(category).strip(),
                "content": content.strip(),
                "metadata": metadata,
            }
        )

    return [item for item in normalized if item["content"]]
