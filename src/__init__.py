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
    db_path = database_path or os.getenv("TCC_DB_PATH", "data/comparisons.db")
    resolved_report_dir = report_dir or os.getenv("TCC_REPORT_DIR", "reports")
    repository = SQLiteComparisonRepository(db_path)
    service = ComparisonService(repository)

    app.config["comparison_service"] = service
    app.config["database_path"] = db_path
    app.config["report_dir"] = resolved_report_dir
    app.config["MAX_CONTENT_LENGTH"] = max_upload_bytes
    app.config["UPLOAD_MAX_BYTES"] = max_upload_bytes
    app.config["APP_NAME"] = "tcc_similarity"

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
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
    )

    app.register_blueprint(api_bp)

    return app
