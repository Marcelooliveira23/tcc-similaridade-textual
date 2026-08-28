import concurrent.futures
import json
import sys
import time
from pathlib import Path
from statistics import median

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src import create_app


def run_load(total_requests: int = 50, workers: int = 10) -> dict:
    app = create_app(database_path=":memory:")

    latencies = []
    statuses = {}

    def worker(i: int):
        client = app.test_client()
        payload = {
            "pairs": [
                {
                    "text_a": f"codigo python {i}",
                    "text_b": f"codigo python {i + 1}",
                    "format": "python",
                }
            ]
        }
        t0 = time.perf_counter()
        response = client.post("/benchmark/performance", json=payload)
        dt = (time.perf_counter() - t0) * 1000
        return response.status_code, dt

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(worker, i) for i in range(total_requests)]
        for f in concurrent.futures.as_completed(futures):
            status, dt = f.result()
            latencies.append(dt)
            statuses[status] = statuses.get(status, 0) + 1

    latencies_sorted = sorted(latencies)
    p95_index = max(0, min(len(latencies_sorted) - 1, int(0.95 * (len(latencies_sorted) - 1))))

    return {
        "requests": total_requests,
        "workers": workers,
        "status_count": statuses,
        "mean_ms": round(sum(latencies) / len(latencies), 4),
        "median_ms": round(median(latencies), 4),
        "p95_ms": round(latencies_sorted[p95_index], 4),
    }


if __name__ == "__main__":
    result = run_load()
    print(json.dumps(result, ensure_ascii=False, indent=2))
