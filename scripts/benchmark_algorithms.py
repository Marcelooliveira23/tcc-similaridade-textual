import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src import create_app


def load_dataset(dataset_path: str) -> list[dict]:
    with open(dataset_path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if isinstance(payload, dict):
        pairs = payload.get("pairs", [])
    elif isinstance(payload, list):
        pairs = payload
    else:
        raise ValueError("Dataset deve ser uma lista de pares ou um objeto com a chave 'pairs'.")

    if not isinstance(pairs, list) or not pairs:
        raise ValueError("Dataset sem pares para benchmark.")

    return pairs


def run_benchmark(dataset_path: str, output_path: str | None = None, max_pairs: int | None = None) -> dict:
    pairs = load_dataset(dataset_path)
    if max_pairs is not None:
        pairs = pairs[:max_pairs]

    app = create_app(database_path=":memory:", report_dir="reports")
    service = app.config["comparison_service"]
    report_data = service.compare_algorithms(pairs)

    summary = {
        "generated_at": report_data["generated_at"],
        "samples": report_data["samples"],
        "winner": report_data["ranking"][0]["algorithm"] if report_data.get("ranking") else None,
        "thresholds": report_data["thresholds"],
        "ranking": report_data["ranking"],
    }

    target = output_path or os.getenv("TCC_BENCHMARK_OUTPUT", "reports/benchmark_summary.json")
    output_file = Path(target)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Executa benchmark automatizado dos algoritmos de similaridade textual.")
    parser.add_argument("--dataset", default=os.getenv("TCC_BENCHMARK_DATASET", "data/datasets/base_pairs.json"))
    parser.add_argument("--output", default=os.getenv("TCC_BENCHMARK_OUTPUT", "reports/benchmark_summary.json"))
    parser.add_argument("--max-pairs", type=int, default=None)
    args = parser.parse_args()

    summary = run_benchmark(args.dataset, output_path=args.output, max_pairs=args.max_pairs)
    print(json.dumps({"winner": summary["winner"], "samples": summary["samples"], "output": args.output}, ensure_ascii=False))


if __name__ == "__main__":
    main()
