import os
import tempfile
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


def test_compare_texts_validation_error(client):
    response = client.post("/compare", json={"text_a": "", "text_b": "ok"})

    assert response.status_code == 400


def test_history_returns_saved_comparisons(client):
    client.post("/compare", json={"text_a": "a", "text_b": "b"})
    response = client.get("/history")

    assert response.status_code == 200
    history = response.get_json()
    assert isinstance(history, list)
    assert len(history) == 1


def test_compare_files_success(client):
    data = {
        "file_a": (BytesIO(b"texto de teste A"), "a.txt"),
        "file_b": (BytesIO(b"texto de teste B"), "b.txt"),
    }
    response = client.post("/compare-files", data=data, content_type="multipart/form-data")

    assert response.status_code == 201
    body = response.get_json()
    assert "id" in body


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
