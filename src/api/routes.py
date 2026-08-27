import csv
import json
import os
from io import StringIO

from flask import Blueprint, current_app, jsonify, make_response, render_template, request

from src.api.file_extractor import extract_text, SUPPORTED_EXTENSIONS

api_bp = Blueprint("api", __name__)


def _validate_texts(text_a: str, text_b: str):
    if not isinstance(text_a, str) or not isinstance(text_b, str):
        return jsonify({"error": "text_a e text_b devem ser strings"}), 400

    if not text_a.strip() or not text_b.strip():
        return jsonify({"error": "text_a e text_b nao podem ser vazios"}), 400

    return None


def _decode_file_text(file_storage) -> str:
    """Mantido por compatibilidade — use extract_text() para multi-formato."""
    raw = file_storage.read()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1", errors="ignore")


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

    validation_error = _validate_texts(text_a, text_b)
    if validation_error:
        return validation_error

    service = current_app.config["comparison_service"]
    result = service.compare_and_store(text_a, text_b)

    return jsonify(result), 201


@api_bp.post("/compare-files")
def compare_files():
    file_a = request.files.get("file_a")
    file_b = request.files.get("file_b")

    if not file_a or not file_b:
        return jsonify({"error": "file_a e file_b sao obrigatorios"}), 400

    text_a, err_a = extract_text(file_a)
    text_b, err_b = extract_text(file_b)

    if err_a:
        return jsonify({"error": f"Arquivo A: {err_a}"}), 422
    if err_b:
        return jsonify({"error": f"Arquivo B: {err_b}"}), 422

    validation_error = _validate_texts(text_a, text_b)
    if validation_error:
        return validation_error

    service = current_app.config["comparison_service"]
    result = service.compare_and_store(text_a, text_b)
    result["file_a"] = file_a.filename
    result["file_b"] = file_b.filename
    return jsonify(result), 201


@api_bp.get("/supported-formats")
def supported_formats():
    """Retorna lista de extensoes de arquivo suportadas."""
    return jsonify({"formats": sorted(SUPPORTED_EXTENSIONS)})


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


@api_bp.post("/report/generate")
def generate_algorithm_report():
    payload = request.get_json(silent=True) or {}
    pairs = payload.get("pairs")
    thresholds = payload.get("thresholds")

    if pairs is None:
        dataset_path = payload.get("dataset_path", "data/datasets/base_pairs.json")
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
