import os
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="requires TEST_DATABASE_URL with PostgreSQL + pgvector")
def test_reindex_endpoint_returns_contract(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setenv("KNOWLEDGE_DIR", str(tmp_path / "knowledge"))
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin")
    monkeypatch.setenv("EMBEDDINGS_PROVIDER", "hash")
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("EMBEDDINGS_VECTOR_DIMENSIONS", "16")
    monkeypatch.setenv("VECTOR_DIMENSIONS", "16")
    monkeypatch.setenv("RETRIEVAL_STRATEGY", "hybrid")
    monkeypatch.setenv("RETRIEVAL_MIN_SCORE", "0.0")

    knowledge_json = tmp_path / "knowledge" / "json"
    knowledge_json.mkdir(parents=True)
    (knowledge_json / "processo_teste.sagai.json").write_text(
        '{"title":"Processo fictício","category":"testes","content":"Para concluir o processo ALFA, acesse Testes > Processo ALFA."}',
        encoding="utf-8",
    )

    from app.config.settings import get_settings

    get_settings.cache_clear()
    from app.main import app

    with TestClient(app) as client:
        response = client.post("/api/v1/knowledge/reindex", headers={"X-Admin-Key": "test-admin"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in {"success", "partial_success"}
        assert data["provider"] == "hash"
        assert data["chunks_indexed"] >= 1
        assert data["sources_processed"] >= 1
        assert data["sources_indexed"] == data["sources_processed"]

        chat = client.post(
            "/api/v1/chat/ask",
            json={"question": "Como concluir o processo ALFA?", "top_k": 3},
        )
        assert chat.status_code == 200
        chat_data = chat.json()
        assert chat_data["retrieval"]["strategy"] == "hybrid"
        assert chat_data["sources"]
        assert "retrieval" in chat_data["sources"][0]

        job = client.post(
            "/api/v1/knowledge/reindex-jobs",
            headers={"X-Admin-Key": "test-admin"},
            json={"requested_by": "pytest"},
        )
        assert job.status_code == 202
        job_data = job.json()
        assert job_data["id"]
        assert job_data["status"] in {"pending", "running", "success", "partial_success", "failed"}
        assert job_data["requested_by"] == "pytest"

        job_detail = None
        for _ in range(20):
            detail = client.get(f"/api/v1/knowledge/reindex-jobs/{job_data['id']}")
            assert detail.status_code == 200
            job_detail = detail.json()
            if job_detail["status"] in {"success", "partial_success", "failed"}:
                break
            time.sleep(0.1)

        assert job_detail is not None
        assert job_detail["status"] in {"success", "partial_success"}
        assert job_detail["sources_total"] >= 1
        assert job_detail["sources_processed"] >= 1
        assert job_detail["chunks_indexed"] >= 1
        assert job_detail["metadata"]["provider"] == "hash"
