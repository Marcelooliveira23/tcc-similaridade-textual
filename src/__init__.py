import os

from flask import Flask

from .api.routes import api_bp
from .repositories.sqlite import SQLiteComparisonRepository
from .services.comparison_service import ComparisonService


def create_app(database_path: str | None = None, report_dir: str | None = None) -> Flask:
    app = Flask(__name__)

    db_path = database_path or os.getenv("TCC_DB_PATH", "data/comparisons.db")
    resolved_report_dir = report_dir or os.getenv("TCC_REPORT_DIR", "reports")
    repository = SQLiteComparisonRepository(db_path)
    service = ComparisonService(repository)

    app.config["comparison_service"] = service
    app.config["database_path"] = db_path
    app.config["report_dir"] = resolved_report_dir
    app.register_blueprint(api_bp)

    return app
