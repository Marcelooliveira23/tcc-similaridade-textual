import csv
from concurrent.futures import ThreadPoolExecutor
import json
import logging
import os
import threading
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from uuid import uuid4

from flask import Blueprint, current_app, jsonify, make_response, render_template, request

from src.api.file_extractor import SUPPORTED_EXTENSIONS, extract_text_from_bytes

logger = logging.getLogger("tcc_similarity.api")
api_bp = Blueprint("api", __name__)
_jobs_lock = threading.Lock()
_jobs: dict[str, dict] = {}
_job_executor: ThreadPoolExecutor | None = None


def _get_job_executor() -> ThreadPoolExecutor:
    global _job_executor
    if _job_executor is None:
        workers = int(current_app.config.get("ASYNC_WORKERS", 2))
        _job_executor = ThreadPoolExecutor(max_workers=max(1, workers))
    return _job_executor


def _job_set(job_id: str, payload: dict) -> None:
    with _jobs_lock:
        _jobs[job_id] = payload


def _job_get(job_id: str) -> dict | None:
    with _jobs_lock:
        return _jobs.get(job_id)


def _is_local_request() -> bool:
    host = (request.host or "").split(":", 1)[0].lower()
    if not host:
        return False
    if host in {"localhost", "127.0.0.1", "::1", "[::1]"}:
        return True
    return host.startswith("127.")


def _require_local_access():
    if not current_app.config.get("LOCAL_ONLY", True):
        return None

    if _is_local_request():
        return None

    logger.warning(
        "blocked_non_local_access %s",
        json.dumps({"host": request.host, "path": request.path}, ensure_ascii=False, sort_keys=True),
    )
    return jsonify({"error": "Acesso restrito ao ambiente local. Este app foi configurado para uso local apenas."}), 403


@api_bp.before_app_request
def _enforce_local_only():
    if request.endpoint in {"api.index", "api.health_check", "api.supported_formats"}:
        return None

    response = _require_local_access()
    if response is not None:
        return response


def _validate_texts(text_a: str, text_b: str, max_chars: int):
    if not isinstance(text_a, str) or not isinstance(text_b, str):
        return jsonify({"error": "text_a e text_b devem ser strings"}), 400

    if not text_a.strip() or not text_b.strip():
        return jsonify({"error": "text_a e text_b nao podem ser vazios"}), 400

    if len(text_a) > max_chars or len(text_b) > max_chars:
        return (
            jsonify({"error": f"text_a/text_b excedem o limite de {max_chars} caracteres."}),
            413,
        )

    return None


def _resolve_dataset_path(dataset_path: str) -> str:
    datasets_dir = (Path(current_app.root_path).parent / "data" / "datasets").resolve()
    candidate = Path(dataset_path)

    if not candidate.is_absolute():
        candidate = (Path.cwd() / candidate).resolve()
    else:
        candidate = candidate.resolve()

    if candidate.suffix.lower() != ".json":
        raise ValueError("dataset_path deve apontar para arquivo .json")

    if datasets_dir != candidate and datasets_dir not in candidate.parents:
        raise ValueError("dataset_path deve estar dentro de data/datasets")

    return str(candidate)


def _decode_file_text(file_storage) -> str:
    """Mantido por compatibilidade — use extract_text() para multi-formato."""
    raw = file_storage.read()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1", errors="ignore")


def _check_upload_limit(file_storage, label: str):
    max_bytes = int(current_app.config.get("MAX_CONTENT_LENGTH", 2 * 1024 * 1024))
    per_ext_limits = current_app.config.get("UPLOAD_MAX_BYTES_BY_EXT", {})
    if not file_storage:
        return None

    try:
        file_storage.stream.seek(0, os.SEEK_END)
        size = file_storage.stream.tell()
        file_storage.stream.seek(0)
    except (AttributeError, OSError):
        size = 0

    filename = getattr(file_storage, "filename", "unknown")
    ext = Path(filename).suffix.lower()
    effective_limit = int(per_ext_limits.get(ext, max_bytes))

    if size > effective_limit:
        logger.warning(
            "upload_limit_exceeded %s",
            json.dumps(
                {
                    "label": label,
                    "file_name": filename,
                    "file_ext": ext,
                    "size_bytes": size,
                    "max_bytes": effective_limit,
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
        )
        return (
            jsonify({"error": f"Arquivo {label} excede o limite máximo de {effective_limit / (1024 * 1024):.1f} MB."}),
            413,
        )
    return None


def _compare_file_payload(service, file_name_a: str, raw_a: bytes, file_name_b: str, raw_b: bytes, max_chars: int) -> dict:
    text_a, err_a = extract_text_from_bytes(raw_a, file_name_a)
    if err_a:
        raise ValueError(f"Arquivo A: {err_a}")

    text_b, err_b = extract_text_from_bytes(raw_b, file_name_b)
    if err_b:
        raise ValueError(f"Arquivo B: {err_b}")

    if not text_a.strip() or not text_b.strip():
        raise ValueError("text_a e text_b nao podem ser vazios")

    if len(text_a) > max_chars or len(text_b) > max_chars:
        raise ValueError(f"text_a/text_b excedem o limite de {max_chars} caracteres.")

    result = service.compare_and_store(text_a, text_b)
    result["file_a"] = file_name_a
    result["file_b"] = file_name_b
    return result


def _run_async_file_job(job_id: str, service, file_name_a: str, raw_a: bytes, file_name_b: str, raw_b: bytes, max_chars: int) -> None:
    _job_set(
        job_id,
        {
            "status": "running",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "result": None,
            "error": None,
        },
    )

    try:
        result = _compare_file_payload(service, file_name_a, raw_a, file_name_b, raw_b, max_chars)
        _job_set(
            job_id,
            {
                "status": "completed",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "result": result,
                "error": None,
            },
        )
    except Exception as exc:  # pragma: no cover - defensive job handling
        _job_set(
            job_id,
            {
                "status": "failed",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "result": None,
                "error": str(exc),
            },
        )


@api_bp.get("/")
def index():
    return render_template("index.html")


@api_bp.get("/health")
def health_check():
    return jsonify({"status": "ok"})


@api_bp.post("/compare")
def compare_texts():
    payload = request.get_json(silent=True) or {}

    text_a = payload.get("text_a", "")
    text_b = payload.get("text_b", "")

    max_chars = int(current_app.config.get("MAX_TEXT_CHARS", 100_000))
    validation_error = _validate_texts(text_a, text_b, max_chars=max_chars)
    if validation_error:
        logger.warning(
            "comparison_validation_failed %s",
            json.dumps({"route": "/compare", "text_a_length": len(text_a), "text_b_length": len(text_b)}, ensure_ascii=False),
        )
        return validation_error

    service = current_app.config["comparison_service"]
    try:
        result = service.compare_and_store(text_a, text_b)
        logger.info(
            "comparison_completed %s",
            json.dumps({"route": "/compare", "stored_id": result.get("id"), "text_lengths": {"a": len(text_a), "b": len(text_b)}}, ensure_ascii=False),
        )
        return jsonify(result), 201
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("comparison_failed %s", json.dumps({"route": "/compare"}, ensure_ascii=False))
        return jsonify({"error": f"Erro ao comparar textos: {exc}"}), 500


@api_bp.post("/compare-files")
def compare_files():
    file_a = request.files.get("file_a")
    file_b = request.files.get("file_b")

    if not file_a or not file_b:
        return jsonify({"error": "file_a e file_b sao obrigatorios"}), 400

    limit_error = _check_upload_limit(file_a, "A")
    if limit_error:
        return limit_error
    limit_error = _check_upload_limit(file_b, "B")
    if limit_error:
        return limit_error

    raw_a = file_a.read()
    raw_b = file_b.read()
    max_chars = int(current_app.config.get("MAX_TEXT_CHARS", 100_000))

    async_threshold = int(current_app.config.get("ASYNC_COMPARE_THRESHOLD_BYTES", 1024 * 1024))
    should_async = len(raw_a) >= async_threshold or len(raw_b) >= async_threshold

    service = current_app.config["comparison_service"]

    if should_async:
        job_id = uuid4().hex
        _job_set(
            job_id,
            {
                "status": "queued",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "result": None,
                "error": None,
            },
        )
        _get_job_executor().submit(
            _run_async_file_job,
            job_id,
            service,
            file_a.filename or "",
            raw_a,
            file_b.filename or "",
            raw_b,
            max_chars,
        )
        return jsonify({"job_id": job_id, "status": "queued", "check": f"/jobs/{job_id}"}), 202

    try:
        result = _compare_file_payload(service, file_a.filename or "", raw_a, file_b.filename or "", raw_b, max_chars)
        logger.info(
            "comparison_completed %s",
            json.dumps({"route": "/compare-files", "file_a": file_a.filename, "file_b": file_b.filename, "stored_id": result.get("id")}, ensure_ascii=False),
        )
        return jsonify(result), 201
    except ValueError as exc:
        if "limite" in str(exc):
            return jsonify({"error": str(exc)}), 413
        return jsonify({"error": str(exc)}), 422
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("comparison_failed %s", json.dumps({"route": "/compare-files"}, ensure_ascii=False))
        return jsonify({"error": f"Erro ao comparar arquivos: {exc}"}), 500


@api_bp.get("/jobs/<job_id>")
def get_job_status(job_id: str):
    payload = _job_get(job_id)
    if not payload:
        return jsonify({"error": "job_id nao encontrado"}), 404
    return jsonify(payload), 200


@api_bp.get("/supported-formats")
def supported_formats():
    """Retorna lista de extensoes de arquivo suportadas."""
    return jsonify(
        {
            "formats": sorted(SUPPORTED_EXTENSIONS),
            "groups": {
                "office": [".doc", ".docx", ".odt", ".rtf", ".xlsx", ".xlsm"],
                "code": [".py", ".java", ".c", ".cpp", ".h", ".hpp", ".cs", ".html", ".css", ".js", ".ts", ".m"],
                "text": [".txt", ".text", ".md", ".markdown", ".csv", ".json", ".xml", ".yml", ".yaml", ".sql"],
            },
        }
    )


@api_bp.get("/history")
def get_history():
    service = current_app.config["comparison_service"]
    history = service.get_history()
    return jsonify(history)


@api_bp.get("/history/export.csv")
def export_history_csv():
    service = current_app.config["comparison_service"]
    history = service.get_history()

    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "id",
            "created_at",
            "text_a",
            "text_b",
            "tfidf_cosine",
            "jaccard",
            "levenshtein_similarity",
        ],
    )
    writer.writeheader()
    writer.writerows(history)

    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = "attachment; filename=history.csv"
    return response


@api_bp.post("/evaluate")
def evaluate_dataset():
    payload = request.get_json(silent=True) or {}
    pairs = payload.get("pairs", [])
    algorithm = payload.get("algorithm", "tfidf_cosine")
    threshold = float(payload.get("threshold", 0.7))

    if not isinstance(pairs, list) or not pairs:
        return jsonify({"error": "pairs deve ser uma lista nao vazia"}), 400

    service = current_app.config["comparison_service"]

    try:
        result = service.evaluate_pairs(pairs, algorithm=algorithm, threshold=threshold)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(result)


@api_bp.post("/benchmark/performance")
def benchmark_performance():
    payload = request.get_json(silent=True) or {}
    pairs = payload.get("pairs")

    if pairs is None:
        dataset_path = payload.get("dataset_path", "data/datasets/base_pairs.json")
        try:
            dataset_path = _resolve_dataset_path(dataset_path)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        if not os.path.exists(dataset_path):
            return jsonify({"error": f"dataset nao encontrado: {dataset_path}"}), 400

        with open(dataset_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        pairs = loaded.get("pairs", [])

    service = current_app.config["comparison_service"]
    try:
        result = service.benchmark_performance(pairs)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(result), 200


@api_bp.post("/report/generate")
def generate_algorithm_report():
    payload = request.get_json(silent=True) or {}
    pairs = payload.get("pairs")
    thresholds = payload.get("thresholds")

    if pairs is None:
        dataset_path = payload.get("dataset_path", "data/datasets/base_pairs.json")
        try:
            dataset_path = _resolve_dataset_path(dataset_path)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        if not os.path.exists(dataset_path):
            return jsonify({"error": f"dataset nao encontrado: {dataset_path}"}), 400

        with open(dataset_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        pairs = loaded.get("pairs", [])

    if not isinstance(pairs, list) or not pairs:
        return jsonify({"error": "pairs deve ser uma lista nao vazia"}), 400

    service = current_app.config["comparison_service"]

    try:
        report_data = service.compare_algorithms(pairs, thresholds=thresholds)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    markdown = service.build_markdown_report(report_data)

    report_dir = current_app.config.get("report_dir", "reports")
    os.makedirs(report_dir, exist_ok=True)
    filename = f"similarity_report_{report_data['generated_at'].replace(':', '-')}".replace(".", "_") + ".md"
    report_path = os.path.join(report_dir, filename)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    return jsonify(
        {
            "report": report_data,
            "markdown": markdown,
            "report_path": report_path,
        }
    )
