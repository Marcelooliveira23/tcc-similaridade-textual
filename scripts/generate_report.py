import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src import create_app


def main() -> None:
    dataset_path = os.getenv("TCC_DATASET_PATH", "data/datasets/base_pairs.json")

    with open(dataset_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    pairs = payload.get("pairs", [])
    if not pairs:
        raise ValueError("Dataset sem pares para avaliacao")

    app = create_app(database_path=":memory:")
    service = app.config["comparison_service"]
    report_dir = app.config["report_dir"]
    os.makedirs(report_dir, exist_ok=True)

    report_data = service.compare_algorithms(pairs)
    markdown = service.build_markdown_report(report_data)

    filename = f"similarity_report_{report_data['generated_at'].replace(':', '-')}".replace(".", "_") + ".md"
    report_path = os.path.join(report_dir, filename)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(report_path)


if __name__ == "__main__":
    main()
