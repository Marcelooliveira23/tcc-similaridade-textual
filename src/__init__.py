import json
import logging
import os

from flask import Flask, jsonify

from .api.routes import api_bp
from .repositories.sqlite import SQLiteComparisonRepository
from .services.comparison_service import ComparisonService


def create_app(database_path: str | None = None, report_dir: str | None = None) -> Flask:
    app = Flask(__name__)

    max_upload_bytes = int(os.getenv("TCC_MAX_UPLOAD_BYTES", 2 * 1024 * 1024))
    max_text_chars = int(os.getenv("TCC_MAX_TEXT_CHARS", 100_000))
    cache_max_items = int(os.getenv("TCC_CACHE_MAX_ITEMS", "1024"))
    async_threshold_bytes = int(os.getenv("TCC_ASYNC_COMPARE_THRESHOLD_BYTES", str(1024 * 1024)))
    async_workers = int(os.getenv("TCC_ASYNC_WORKERS", "2"))

    try:
        max_upload_bytes_by_ext = json.loads(os.getenv("TCC_MAX_UPLOAD_BYTES_BY_EXT", "{}"))
        if not isinstance(max_upload_bytes_by_ext, dict):
            max_upload_bytes_by_ext = {}
    except json.JSONDecodeError:
        max_upload_bytes_by_ext = {}

    normalized_limits = {
        str(k).lower(): int(v)
        for k, v in max_upload_bytes_by_ext.items()
        if isinstance(k, str)
    }

    db_path = database_path or os.getenv("TCC_DB_PATH", "data/comparisons.db")
    resolved_report_dir = report_dir or os.getenv("TCC_REPORT_DIR", "reports")
    local_only = os.getenv("TCC_LOCAL_ONLY", "true").strip().lower() not in {"0", "false", "no"}
    repository = SQLiteComparisonRepository(db_path)
    service = ComparisonService(repository, cache_max_items=cache_max_items)

    app.config["comparison_service"] = service
    app.config["database_path"] = db_path
    app.config["report_dir"] = resolved_report_dir
    app.config["MAX_CONTENT_LENGTH"] = max_upload_bytes
    app.config["UPLOAD_MAX_BYTES"] = max_upload_bytes
    app.config["UPLOAD_MAX_BYTES_BY_EXT"] = normalized_limits
    app.config["ASYNC_COMPARE_THRESHOLD_BYTES"] = async_threshold_bytes
    app.config["ASYNC_WORKERS"] = async_workers
    app.config["MAX_TEXT_CHARS"] = max_text_chars
    app.config["APP_NAME"] = "tcc_similarity"
    app.config["LOCAL_ONLY"] = local_only

    app.logger.setLevel(logging.INFO)
    if not app.logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
        app.logger.addHandler(handler)

    @app.errorhandler(413)
    def request_too_large(error):
        return jsonify({"error": f"Arquivo excede o limite máximo de {max_upload_bytes / (1024 * 1024):.1f} MB."}), 413

    app.logger.info(
        "app_initialized %s",
        json.dumps(
            {
                "database_path": db_path,
                "report_dir": resolved_report_dir,
                "max_upload_bytes": max_upload_bytes,
                "max_upload_bytes_by_ext": normalized_limits,
                "max_text_chars": max_text_chars,
                "cache_max_items": cache_max_items,
                "async_compare_threshold_bytes": async_threshold_bytes,
                "async_workers": async_workers,
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
    )

    app.register_blueprint(api_bp)

    return app
