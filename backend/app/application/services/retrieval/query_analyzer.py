from __future__ import annotations

import re
import unicodedata

_PORTUGUESE_STOPWORDS = {
    "a", "ao", "aos", "as", "com", "como", "da", "das", "de", "do", "dos",
    "e", "em", "essa", "esse", "esta", "este", "eu", "isso", "no", "nos", "na",
    "nas", "o", "os", "ou", "para", "por", "que", "qual", "quais", "quando",
    "se", "sem", "sobre", "um", "uma", "uns", "umas", "me", "minha", "meu",
    "pelo", "pela", "pelos", "pelas", "dentro", "sistema", "maxmanager",
}

_TOKEN_RE = re.compile(r"[\wÀ-ÿ]{2,}", re.UNICODE)


def strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(character for character in normalized if not unicodedata.combining(character))


def normalize_query(value: str) -> str:
    value = strip_accents(value.lower().strip())
    value = re.sub(r"[^a-z0-9_\s-]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def extract_query_terms(value: str, *, max_terms: int = 12) -> list[str]:
    normalized = normalize_query(value)
    terms: list[str] = []
    seen: set[str] = set()
    for match in _TOKEN_RE.finditer(normalized):
        term = match.group(0)
        if term in _PORTUGUESE_STOPWORDS or len(term) < 2 or term in seen:
            continue
        seen.add(term)
        terms.append(term)
        if len(terms) >= max_terms:
            break
    return terms
