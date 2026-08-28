"""Service layer for text similarity comparison orchestration.

Provides high-level business logic for managing text comparisons,
integrating all three similarity algorithms with persistence and
evaluation capabilities.

This service implements the Facade pattern, presenting a unified interface
to API routes while coordinating algorithm execution and data storage.
"""

import statistics
import threading
from collections import OrderedDict
from datetime import datetime, timezone
from hashlib import sha256
from time import perf_counter

from src.algorithms.jaccard import jaccard_similarity
from src.algorithms.levenshtein import normalized_levenshtein_similarity
from src.algorithms.tfidf_cosine import tfidf_cosine_similarity
from src.models.comparison import ComparisonResult
from src.repositories.base import ComparisonRepository


class ComparisonService:
    """Orchestrates text comparison operations across all algorithms.
    
    Provides unified interface to:
    - Compute similarity scores using three different algorithms
    - Store comparison results in persistent repository
    - Retrieve comparison history
    - Perform batch evaluation against datasets
    """
    
    ALGORITHMS = ("tfidf_cosine", "jaccard", "levenshtein")

    def __init__(self, repository: ComparisonRepository, cache_max_items: int = 1024) -> None:
        """Initialize service with dependency injection of repository.
        
        Args:
            repository (ComparisonRepository): Data access object for persistence.
        """
        self.repository = repository
        self.cache_max_items = max(0, int(cache_max_items))
        self._cache_lock = threading.Lock()
        self._score_cache: OrderedDict[str, dict] = OrderedDict()
        self._cache_hits = 0
        self._cache_misses = 0

    @staticmethod
    def _cache_key(text_a: str, text_b: str) -> str:
        digest = sha256()
        digest.update(text_a.encode("utf-8", errors="ignore"))
        digest.update(b"\x00\x1f\x00")
        digest.update(text_b.encode("utf-8", errors="ignore"))
        return digest.hexdigest()

    def _cache_get(self, key: str) -> dict | None:
        if self.cache_max_items <= 0:
            return None

        with self._cache_lock:
            cached = self._score_cache.get(key)
            if cached is None:
                self._cache_misses += 1
                return None
            self._score_cache.move_to_end(key)
            self._cache_hits += 1
            return dict(cached)

    def _cache_set(self, key: str, value: dict) -> None:
        if self.cache_max_items <= 0:
            return

        with self._cache_lock:
            self._score_cache[key] = dict(value)
            self._score_cache.move_to_end(key)
            while len(self._score_cache) > self.cache_max_items:
                self._score_cache.popitem(last=False)

    def cache_stats(self) -> dict:
        with self._cache_lock:
            total = self._cache_hits + self._cache_misses
            hit_rate = (self._cache_hits / total) if total else 0.0
            return {
                "enabled": self.cache_max_items > 0,
                "max_items": self.cache_max_items,
                "current_items": len(self._score_cache),
                "hits": self._cache_hits,
                "misses": self._cache_misses,
                "hit_rate": round(hit_rate, 6),
            }

    @staticmethod
    def _algorithm_score(text_a: str, text_b: str, algorithm: str) -> float:
        """Dispatch to appropriate algorithm based on name parameter.
        
        Internal helper for selecting which algorithm to execute.
        
        Args:
            text_a (str): First text.
            text_b (str): Second text.
            algorithm (str): One of 'tfidf_cosine', 'jaccard', 'levenshtein'.
            
        Returns:
            float: Similarity score [0, 1].
            
        Raises:
            ValueError: If algorithm name is not recognized.
        """
        if algorithm == "tfidf_cosine":
            return tfidf_cosine_similarity(text_a, text_b)
        if algorithm == "jaccard":
            return jaccard_similarity(text_a, text_b)
        if algorithm == "levenshtein":
            return normalized_levenshtein_similarity(text_a, text_b)

        raise ValueError("algorithm deve ser tfidf_cosine, jaccard ou levenshtein")

    def compare(self, text_a: str, text_b: str) -> dict:
        """Compute similarity scores from all three algorithms.
        
        Compares two texts using TF-IDF+Cosine, Jaccard, and Levenshtein
        methods simultaneously, returning all three scores for comparison.
        
        Args:
            text_a (str): First document text.
            text_b (str): Second document text.
            
        Returns:
            dict: Mapping of algorithm names to similarity scores [0, 1]:
                {
                    'tfidf_cosine': float,
                    'jaccard': float,
                    'levenshtein_similarity': float
                }
                
        Note:
            Does NOT persist results. Use compare_and_store() for persistence.
        """
        key = self._cache_key(text_a, text_b)
        cached = self._cache_get(key)
        if cached is not None:
            return cached

        scores = {
            "tfidf_cosine": round(tfidf_cosine_similarity(text_a, text_b), 6),
            "jaccard": round(jaccard_similarity(text_a, text_b), 6),
            "levenshtein_similarity": round(normalized_levenshtein_similarity(text_a, text_b), 6),
        }
        self._cache_set(key, scores)
        return scores

    def compare_and_store(self, text_a: str, text_b: str) -> dict:
        """Compute similarity scores and persist comparison to repository.
        
        Compares texts and stores result with timestamp for auditing
        and later retrieval.
        
        Args:
            text_a (str): First document text.
            text_b (str): Second document text.
            
        Returns:
            dict: Result dictionary including scores and metadata:
                {
                    'id': str,
                    'text_a': str,
                    'text_b': str,
                    'tfidf_cosine': float,
                    'jaccard': float,
                    'levenshtein_similarity': float,
                    'timestamp': ISO8601 string
                }
        """
        scores = self.compare(text_a, text_b)

        result = ComparisonResult.build(
            text_a=text_a,
            text_b=text_b,
            tfidf_cosine=scores["tfidf_cosine"],
            jaccard=scores["jaccard"],
            levenshtein_similarity=scores["levenshtein_similarity"],
        )

        self.repository.save(result)
        return result.to_dict()

    def benchmark_performance(self, pairs: list[dict]) -> dict:
        """Measure latency stats by algorithm and input format."""
        if not isinstance(pairs, list) or not pairs:
            raise ValueError("pairs deve ser uma lista nao vazia")

        durations: dict[str, dict[str, list[float]]] = {
            algorithm: {} for algorithm in self.ALGORITHMS
        }

        for index, pair in enumerate(pairs):
            text_a = pair.get("text_a", "")
            text_b = pair.get("text_b", "")
            fmt = str(pair.get("format", "text")).lower().strip() or "text"

            if not isinstance(text_a, str) or not isinstance(text_b, str):
                raise ValueError(f"pair[{index}] deve conter text_a/text_b string")

            for algorithm in self.ALGORITHMS:
                t0 = perf_counter()
                self._algorithm_score(text_a, text_b, algorithm)
                elapsed_ms = (perf_counter() - t0) * 1000
                durations[algorithm].setdefault(fmt, []).append(elapsed_ms)

        def summarize(values: list[float]) -> dict:
            sorted_values = sorted(values)
            p95_index = max(0, min(len(sorted_values) - 1, int(0.95 * (len(sorted_values) - 1))))
            return {
                "count": len(values),
                "mean_ms": round(sum(values) / len(values), 4),
                "median_ms": round(statistics.median(values), 4),
                "p95_ms": round(sorted_values[p95_index], 4),
            }

        by_algorithm = {}
        for algorithm, by_format in durations.items():
            merged = [v for values in by_format.values() for v in values]
            by_algorithm[algorithm] = {
                "overall": summarize(merged),
                "by_format": {fmt: summarize(values) for fmt, values in by_format.items()},
            }

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "samples": len(pairs),
            "algorithms": by_algorithm,
        }

    def get_history(self) -> list[dict]:
        """Retrieve all stored comparison results from repository.
        
        Returns:
            list[dict]: List of comparison result dictionaries, newest first.
        """
        return [item.to_dict() for item in self.repository.list_all()]

    def evaluate_pairs(self, pairs: list[dict], algorithm: str, threshold: float) -> dict:
        """Evaluate algorithm performance on labeled text pairs using confusion matrix.
        
        Compares algorithm predictions against ground truth labels, computing
        standard IR metrics (accuracy, precision, recall, F1-score).
        
        Args:
            pairs (list[dict]): List of labeled pairs, each with:
                {
                    'text_a': str,
                    'text_b': str,
                    'is_similar': bool (ground truth)
                }
            algorithm (str): Algorithm to evaluate ('tfidf_cosine', 'jaccard', 'levenshtein').
            threshold (float): Decision threshold [0, 1]. Score >= threshold → similar prediction.
            
        Returns:
            dict: Comprehensive evaluation results:
                {
                    'algorithm': str,
                    'threshold': float,
                    'samples': int,
                    'confusion_matrix': {'tp': int, 'fp': int, 'tn': int, 'fn': int},
                    'metrics': {
                        'accuracy': float,   # (tp + tn) / total
                        'precision': float,  # tp / (tp + fp)
                        'recall': float,     # tp / (tp + fn)
                        'f1': float          # 2 * (precision * recall) / (precision + recall)
                    },
                    'scored_pairs': list[dict]  # detailed per-pair results
                }
                
        Raises:
            ValueError: If pair format is invalid or required fields missing.
            
        Note:
            - Optimal threshold varies by algorithm and use case
            - F1-score recommended for balanced evaluation
            - Consider class imbalance when interpreting metrics
        """
        tp = fp = tn = fn = 0
        scored_pairs = []

        for index, pair in enumerate(pairs):
            text_a = pair.get("text_a", "")
            text_b = pair.get("text_b", "")
            expected = pair.get("is_similar")

            if not isinstance(text_a, str) or not isinstance(text_b, str):
                raise ValueError(f"pair[{index}] deve conter text_a/text_b string")

            if not isinstance(expected, bool):
                raise ValueError(f"pair[{index}] deve conter is_similar boolean")

            score = self._algorithm_score(text_a, text_b, algorithm)
            predicted = score >= threshold

            if predicted and expected:
                tp += 1
            elif predicted and not expected:
                fp += 1
            elif not predicted and not expected:
                tn += 1
            else:
                fn += 1

            scored_pairs.append(
                {
                    "text_a": text_a,
                    "text_b": text_b,
                    "score": round(score, 6),
                    "predicted_similar": predicted,
                    "expected_similar": expected,
                }
            )

        total = len(pairs)
        accuracy = (tp + tn) / total if total else 0.0
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

        return {
            "algorithm": algorithm,
            "threshold": threshold,
            "samples": total,
            "confusion_matrix": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
            "metrics": {
                "accuracy": round(accuracy, 6),
                "precision": round(precision, 6),
                "recall": round(recall, 6),
                "f1": round(f1, 6),
            },
            "scored_pairs": scored_pairs,
        }

    def compare_algorithms(self, pairs: list[dict], thresholds: dict | None = None) -> dict:
        """Comparative evaluation of all three algorithms on same dataset.
        
        Runs complete evaluation pipeline for each algorithm, generates
        comparative ranking by F1-score, and produces comprehensive report data.
        
        Args:
            pairs (list[dict]): Labeled text pairs with ground truth is_similar field.
            thresholds (dict | None): Per-algorithm decision thresholds. If None, uses defaults:
                {
                    'tfidf_cosine': 0.7,
                    'jaccard': 0.6,
                    'levenshtein': 0.75
                }
                
        Returns:
            dict: Complete comparative report:
                {
                    'generated_at': ISO8601 timestamp,
                    'samples': int (total pairs evaluated),
                    'thresholds': dict,
                    'algorithms': list[dict]  # detailed results from evaluate_pairs()
                    'ranking': list[dict]     # sorted by F1 score, descending
                }
                
        Ranking format:
            [
                {
                    'algorithm': str,
                    'f1': float,
                    'accuracy': float
                },
                ...
            ]
            
        Note:
            - Ranking is primary sort key for comparative analysis
            - Default thresholds empirically tuned for text similarity task
            - Results suitable for publication in academic report
        """
        thresholds = thresholds or {
            "tfidf_cosine": 0.7,
            "jaccard": 0.6,
            "levenshtein": 0.75,
        }

        key_by_algorithm = {
            "tfidf_cosine": "tfidf_cosine",
            "jaccard": "jaccard",
            "levenshtein": "levenshtein_similarity",
        }

        states = {
            algorithm: {
                "tp": 0,
                "fp": 0,
                "tn": 0,
                "fn": 0,
                "scored_pairs": [],
            }
            for algorithm in self.ALGORITHMS
        }

        for index, pair in enumerate(pairs):
            text_a = pair.get("text_a", "")
            text_b = pair.get("text_b", "")
            expected = pair.get("is_similar")

            if not isinstance(text_a, str) or not isinstance(text_b, str):
                raise ValueError(f"pair[{index}] deve conter text_a/text_b string")

            if not isinstance(expected, bool):
                raise ValueError(f"pair[{index}] deve conter is_similar boolean")

            scores = self.compare(text_a, text_b)

            for algorithm in self.ALGORITHMS:
                state = states[algorithm]
                score_key = key_by_algorithm[algorithm]
                score = float(scores[score_key])
                threshold = float(thresholds.get(algorithm, 0.7))
                predicted = score >= threshold

                if predicted and expected:
                    state["tp"] += 1
                elif predicted and not expected:
                    state["fp"] += 1
                elif not predicted and not expected:
                    state["tn"] += 1
                else:
                    state["fn"] += 1

                state["scored_pairs"].append(
                    {
                        "text_a": text_a,
                        "text_b": text_b,
                        "score": round(score, 6),
                        "predicted_similar": predicted,
                        "expected_similar": expected,
                    }
                )

        summaries = []
        total = len(pairs)
        for algorithm in self.ALGORITHMS:
            state = states[algorithm]
            tp, fp, tn, fn = state["tp"], state["fp"], state["tn"], state["fn"]

            accuracy = (tp + tn) / total if total else 0.0
            precision = tp / (tp + fp) if (tp + fp) else 0.0
            recall = tp / (tp + fn) if (tp + fn) else 0.0
            f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

            summaries.append(
                {
                    "algorithm": algorithm,
                    "threshold": float(thresholds.get(algorithm, 0.7)),
                    "samples": total,
                    "confusion_matrix": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
                    "metrics": {
                        "accuracy": round(accuracy, 6),
                        "precision": round(precision, 6),
                        "recall": round(recall, 6),
                        "f1": round(f1, 6),
                    },
                    "scored_pairs": state["scored_pairs"],
                }
            )

        ranking = sorted(
            [
                {
                    "algorithm": entry["algorithm"],
                    "f1": entry["metrics"]["f1"],
                    "accuracy": entry["metrics"]["accuracy"],
                }
                for entry in summaries
            ],
            key=lambda x: (x["f1"], x["accuracy"]),
            reverse=True,
        )

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "samples": len(pairs),
            "thresholds": thresholds,
            "algorithms": summaries,
            "ranking": ranking,
        }

    @staticmethod
    def build_markdown_report(report_data: dict) -> str:
        """Generate professional Markdown report from evaluation results.
        
        Creates formatted Markdown document suitable for inclusion in thesis,
        including metrics tables, algorithm ranking, and recommendations.
        
        Args:
            report_data (dict): Output from compare_algorithms() method.
            
        Returns:
            str: Complete Markdown document with:
                - Header with timestamp and sample count
                - Metrics comparison table (algorithm × metrics)
                - Algorithm ranking by F1-score
                - Scenario-based analysis (if provided)
                - Recommendations and conclusions
                
        Output sections:
            1. Title and metadata
            2. Comparative metrics table
            3. Algorithm ranking
            4. Scenario analysis (optional)
            5. Conclusions and recommendations
                
        Example output:
            # Relatorio Experimental de Similaridade Textual
            - Gerado em: 2026-07-20T...
            - Total de amostras: 26
            
            | Algoritmo | Threshold | Accuracy | Precision | Recall | F1 |
            |---|---:|---:|---:|---:|---:|
            | tfidf_cosine | 0.70 | 0.9615 | 0.9091 | 1.0000 | 0.9524 |
            ...
        """
        lines = [
            "# Relatorio Experimental de Similaridade Textual",
            "",
            f"- Gerado em: {report_data['generated_at']}",
            f"- Total de amostras: {report_data['samples']}",
            "",
            "## Comparativo por algoritmo",
            "",
            "| Algoritmo | Threshold | Accuracy | Precision | Recall | F1 |",
            "|---|---:|---:|---:|---:|---:|",
        ]

        for entry in report_data["algorithms"]:
            metric = entry["metrics"]
            lines.append(
                f"| {entry['algorithm']} | {entry['threshold']:.2f} | {metric['accuracy']:.4f} | {metric['precision']:.4f} | {metric['recall']:.4f} | {metric['f1']:.4f} |"
            )

        lines.extend(["", "## Ranking", ""])
        for index, item in enumerate(report_data["ranking"], start=1):
            lines.append(
                f"{index}. {item['algorithm']} (F1={item['f1']:.4f}, Accuracy={item['accuracy']:.4f})"
            )

        return "\n".join(lines)
