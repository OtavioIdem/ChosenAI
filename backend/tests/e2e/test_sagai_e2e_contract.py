import os

import httpx
import pytest

pytestmark = pytest.mark.e2e

BASE_URL = os.getenv("SAGAI_E2E_BASE_URL")
ADMIN_KEY = os.getenv("SAGAI_E2E_ADMIN_KEY", "change_this_admin_key")


@pytest.mark.skipif(not BASE_URL, reason="requires SAGAI_E2E_BASE_URL pointing to a running SAGAI API")
def test_e2e_reindex_and_chat_contract():
    with httpx.Client(base_url=BASE_URL, timeout=60) as client:
        health = client.get("/health")
        assert health.status_code == 200

        reindex = client.post("/api/v1/knowledge/reindex", headers={"X-Admin-Key": ADMIN_KEY})
        assert reindex.status_code == 200
        reindex_data = reindex.json()
        assert reindex_data["status"] in {"success", "partial_success"}
        assert "chunks_indexed" in reindex_data
        assert "provider" in reindex_data

        ask = client.post(
            "/api/v1/chat/ask",
            json={"question": "O que existe na base sobre financeiro?", "top_k": 3},
        )
        assert ask.status_code == 200
        ask_data = ask.json()
        assert "answer" in ask_data
        assert "sources" in ask_data
        assert "confidence_status" in ask_data
        assert "retrieval" in ask_data


@pytest.mark.skipif(not BASE_URL, reason="requires SAGAI_E2E_BASE_URL pointing to a running SAGAI API")
def test_e2e_no_context_does_not_expose_stacktrace():
    with httpx.Client(base_url=BASE_URL, timeout=60) as client:
        ask = client.post(
            "/api/v1/chat/ask",
            json={"question": "Explique um processo inexistente chamado ZXQ-999 sem contexto", "top_k": 3},
        )
        assert ask.status_code == 200
        body = ask.json()
        assert "traceback" not in body["answer"].lower()
        assert body["confidence_status"] in {"low", "medium", "high"}
