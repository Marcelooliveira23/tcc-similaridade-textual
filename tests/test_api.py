import os
import tempfile
import time
from io import BytesIO

import pytest

from src import create_app


@pytest.fixture
def client():
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    report_dir = tempfile.mkdtemp(prefix="tcc-report-")

    app = create_app(database_path=db_path, report_dir=report_dir)
    test_client = app.test_client()

    yield test_client

    service = app.config["comparison_service"]
    repository = service.repository
    if hasattr(repository, "close"):
        repository.close()

    if os.path.exists(db_path):
        os.remove(db_path)

    if os.path.exists(report_dir):
        for name in os.listdir(report_dir):
            os.remove(os.path.join(report_dir, name))
        os.rmdir(report_dir)


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_index_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Comparador de Similaridade de Textos" in response.data


def test_compare_texts_success(client):
    payload = {"text_a": "texto para comparar", "text_b": "texto para comparar"}
    response = client.post("/compare", json=payload)

    assert response.status_code == 201
    body = response.get_json()
    assert "id" in body
    assert body["tfidf_cosine"] >= 0.99


def test_compare_texts_ai_success(client):
    payload = {"text_a": "def soma(a,b): return a+b", "text_b": "def add(x,y): return x+y"}
    response = client.post("/compare-ai", json=payload)

    assert response.status_code == 200
    body = response.get_json()
    assert "classic" in body
    assert "ai" in body
    assert "ml_semantic" in body["ai"]
    assert 0.0 <= body["ai"]["ml_semantic"] <= 1.0


def test_supported_formats_groups(client):
    response = client.get("/supported-formats")

    assert response.status_code == 200
    body = response.get_json()
    assert "groups" in body
    assert ".py" in body["groups"]["code"]
    assert ".xlsx" in body["groups"]["office"]


def test_compare_texts_validation_error(client):
    response = client.post("/compare", json={"text_a": "", "text_b": "ok"})

    assert response.status_code == 400


def test_compare_texts_rejects_too_long_text(client):
    huge_text = "a" * 100001
    response = client.post("/compare", json={"text_a": huge_text, "text_b": "ok"})

    assert response.status_code == 413
    assert "limite" in response.get_json()["error"].lower()


def test_history_returns_saved_comparisons(client):
    client.post("/compare", json={"text_a": "a", "text_b": "b"})
    response = client.get("/history")

    assert response.status_code == 200
    history = response.get_json()
    assert isinstance(history, list)
    assert len(history) == 1


def test_history_is_blocked_for_non_local_host(client):
    response = client.get("/history", headers={"Host": "example.com"})

    assert response.status_code == 403
    assert "restrito" in response.get_json()["error"].lower()


def test_compare_files_success(client):
    data = {
        "file_a": (BytesIO(b"texto de teste A"), "a.txt"),
        "file_b": (BytesIO(b"texto de teste B"), "b.txt"),
    }
    response = client.post("/compare-files", data=data, content_type="multipart/form-data")

    assert response.status_code == 201
    body = response.get_json()
    assert "id" in body


def test_app_uses_centralized_upload_limits():
    app = create_app(database_path=":memory:", report_dir="reports")

    assert app.config["MAX_CONTENT_LENGTH"] == 2 * 1024 * 1024
    assert app.config["UPLOAD_MAX_BYTES"] == 2 * 1024 * 1024


def test_compare_cache_stats_exposed_by_service():
    app = create_app(database_path=":memory:", report_dir="reports")
    service = app.config["comparison_service"]

    service.compare("texto x", "texto y")
    service.compare("texto x", "texto y")

    stats = service.cache_stats()
    assert stats["enabled"] is True
    assert stats["hits"] >= 1


def test_compare_files_rejects_file_too_large(client):
    oversized = b"A" * (2 * 1024 * 1024 + 1)
    data = {
        "file_a": (BytesIO(oversized), "a.txt"),
        "file_b": (BytesIO(b"texto de teste B"), "b.txt"),
    }
    response = client.post("/compare-files", data=data, content_type="multipart/form-data")

    assert response.status_code == 413
    assert "arquivo" in response.get_json()["error"].lower()


def test_compare_files_respects_extension_limit(client):
    client.application.config["UPLOAD_MAX_BYTES_BY_EXT"] = {".txt": 5}

    data = {
        "file_a": (BytesIO(b"123456"), "a.txt"),
        "file_b": (BytesIO(b"ok"), "b.txt"),
    }
    response = client.post("/compare-files", data=data, content_type="multipart/form-data")

    assert response.status_code == 413


def test_compare_files_async_job_flow(client):
    client.application.config["ASYNC_COMPARE_THRESHOLD_BYTES"] = 1

    data = {
        "file_a": (BytesIO(b"texto de teste A"), "a.txt"),
        "file_b": (BytesIO(b"texto de teste B"), "b.txt"),
    }
    response = client.post("/compare-files", data=data, content_type="multipart/form-data")
    assert response.status_code == 202

    job_id = response.get_json()["job_id"]
    deadline = time.time() + 2
    statuses = {"queued", "running", "completed", "failed"}

    final_payload = None
    while time.time() < deadline:
        poll = client.get(f"/jobs/{job_id}")
        assert poll.status_code == 200
        payload = poll.get_json()
        assert payload["status"] in statuses
        if payload["status"] in {"completed", "failed"}:
            final_payload = payload
            break
        time.sleep(0.05)

    assert final_payload is not None
    assert final_payload["status"] == "completed"


def test_evaluate_dataset_success(client):
    payload = {
        "algorithm": "jaccard",
        "threshold": 0.5,
        "pairs": [
            {"text_a": "banana maca", "text_b": "banana maca", "is_similar": True},
            {"text_a": "carro aviao", "text_b": "banana maca", "is_similar": False},
        ],
    }

    response = client.post("/evaluate", json=payload)
    assert response.status_code == 200

    body = response.get_json()
    assert body["algorithm"] == "jaccard"
    assert body["samples"] == 2
    assert "metrics" in body


def test_benchmark_performance_endpoint(client):
    payload = {
        "pairs": [
            {"text_a": "print('a')", "text_b": "print('b')", "format": "python"},
            {"text_a": "<h1>a</h1>", "text_b": "<h1>b</h1>", "format": "html"},
        ]
    }
    response = client.post("/benchmark/performance", json=payload)
    assert response.status_code == 200
    body = response.get_json()
    assert body["samples"] == 2
    assert "tfidf_cosine" in body["algorithms"]


def test_export_history_csv(client):
    client.post("/compare", json={"text_a": "x", "text_b": "y"})
    response = client.get("/history/export.csv")

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/csv")
    assert "id,created_at" in response.get_data(as_text=True)


def test_generate_algorithm_report_with_dataset_base(client):
    response = client.post("/report/generate", json={})

    assert response.status_code == 200
    body = response.get_json()
    assert "report" in body
    assert "ranking" in body["report"]
    assert "report_path" in body
    assert os.path.exists(body["report_path"])


def test_generate_algorithm_report_rejects_dataset_outside_allowed_dir(client):
    response = client.post(
        "/report/generate",
        json={"dataset_path": "README.md"},
    )

    assert response.status_code == 400
    assert "dataset_path" in response.get_json()["error"]


def test_benchmark_summary_uses_dataset_and_winner():
    from scripts.benchmark_algorithms import run_benchmark

    summary = run_benchmark("data/datasets/base_pairs.json", output_path="reports/test_benchmark_summary.json", max_pairs=5)

    assert summary["samples"] == 5
    assert summary["winner"] in {"tfidf_cosine", "jaccard", "levenshtein"}
    assert os.path.exists("reports/test_benchmark_summary.json")

    if os.path.exists("reports/test_benchmark_summary.json"):
        os.remove("reports/test_benchmark_summary.json")
