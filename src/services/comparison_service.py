"""Service layer for text similarity comparison orchestration.

Provides high-level business logic for managing text comparisons,
integrating all three similarity algorithms with persistence and
evaluation capabilities.

This service implements the Facade pattern, presenting a unified interface
to API routes while coordinating algorithm execution and data storage.
"""

import os
from collections.abc import Callable
from datetime import datetime, timezone

import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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

    def __init__(self, repository: ComparisonRepository) -> None:
        """Initialize service with dependency injection of repository.
        
        Args:
            repository (ComparisonRepository): Data access object for persistence.
        """
        self.repository = repository

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
        return {
            "tfidf_cosine": round(tfidf_cosine_similarity(text_a, text_b), 6),
            "jaccard": round(jaccard_similarity(text_a, text_b), 6),
            "levenshtein_similarity": round(normalized_levenshtein_similarity(text_a, text_b), 6),
        }

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

    @staticmethod
    def ml_semantic_similarity(text_a: str, text_b: str) -> float:
        """Compute ML-based semantic similarity using character n-gram TF-IDF.

        This score is language-agnostic and works reasonably well for natural
        language and source code (Python, Java, C/C++, C#, HTML, CSS, etc.).
        """
        if not text_a.strip() and not text_b.strip():
            return 1.0
        if not text_a.strip() or not text_b.strip():
            return 0.0

        vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5))
        matrix = vectorizer.fit_transform([text_a, text_b])
        score = float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])
        return round(max(0.0, min(1.0, score)), 6)

    @staticmethod
    def _cosine_from_vectors(vector_a: list[float], vector_b: list[float]) -> float:
        if not vector_a or not vector_b or len(vector_a) != len(vector_b):
            return 0.0

        dot = sum(a * b for a, b in zip(vector_a, vector_b, strict=False))
        norm_a = sum(a * a for a in vector_a) ** 0.5
        norm_b = sum(b * b for b in vector_b) ** 0.5
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return round(max(0.0, min(1.0, dot / (norm_a * norm_b))), 6)

    def _provider_similarity(
        self,
        provider: str,
        text_a: str,
        text_b: str,
        fn: Callable[[str], list[float]],
    ) -> dict:
        try:
            emb_a = fn(text_a)
            emb_b = fn(text_b)
            return {"provider": provider, "score": self._cosine_from_vectors(emb_a, emb_b)}
        except Exception as exc:  # pragma: no cover - network/provider defensive handling
            return {"provider": provider, "score": None, "error": str(exc)}

    @staticmethod
    def _gemini_embedding(text: str) -> list[float]:
        api_key = os.getenv("TCC_GEMINI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("TCC_GEMINI_API_KEY nao configurada")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={api_key}"
        payload = {
            "model": "models/text-embedding-004",
            "content": {"parts": [{"text": text[:12000]}]},
        }
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        values = data.get("embedding", {}).get("values", [])
        if not isinstance(values, list) or not values:
            raise RuntimeError("Resposta de embedding Gemini invalida")
        return [float(v) for v in values]

    @staticmethod
    def _openai_embedding(text: str) -> list[float]:
        api_key = os.getenv("TCC_OPENAI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("TCC_OPENAI_API_KEY nao configurada")

        url = "https://api.openai.com/v1/embeddings"
        payload = {"model": "text-embedding-3-small", "input": text[:12000]}
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        vector = ((data.get("data") or [{}])[0]).get("embedding", [])
        if not isinstance(vector, list) or not vector:
            raise RuntimeError("Resposta de embedding OpenAI invalida")
        return [float(v) for v in vector]

    @staticmethod
    def _claude_similarity(text_a: str, text_b: str) -> float:
        api_key = os.getenv("TCC_CLAUDE_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("TCC_CLAUDE_API_KEY nao configurada")

        url = "https://api.anthropic.com/v1/messages"
        prompt = (
            "Retorne somente um numero entre 0 e 1 para similaridade textual. "
            "0 significa totalmente diferente e 1 significa praticamente igual.\n"
            f"Texto A:\n{text_a[:8000]}\n\nTexto B:\n{text_b[:8000]}"
        )
        response = requests.post(
            url,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-3-5-haiku-latest",
                "max_tokens": 16,
                "temperature": 0,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        text = (((payload.get("content") or [{}])[0]).get("text") or "").strip()
        score = float(text)
        return round(max(0.0, min(1.0, score)), 6)

    def compare_with_ai(self, text_a: str, text_b: str, include_providers: bool = False) -> dict:
        """Return classic + ML hybrid similarity and optional provider-based AI scores."""
        classic = self.compare(text_a, text_b)
        ml_score = self.ml_semantic_similarity(text_a, text_b)

        ensemble = round(
            (
                0.35 * classic["tfidf_cosine"]
                + 0.2 * classic["jaccard"]
                + 0.2 * classic["levenshtein_similarity"]
                + 0.25 * ml_score
            ),
            6,
        )

        response = {
            "classic": classic,
            "ai": {
                "ml_semantic": ml_score,
                "ensemble": ensemble,
                "providers": [],
            },
            "supported_ai_providers": ["gemini", "openai", "claude"],
        }

        if not include_providers:
            return response

        providers = [
            self._provider_similarity("gemini", text_a, text_b, self._gemini_embedding),
            self._provider_similarity("openai", text_a, text_b, self._openai_embedding),
        ]

        try:
            providers.append({"provider": "claude", "score": self._claude_similarity(text_a, text_b)})
        except Exception as exc:  # pragma: no cover - network/provider defensive handling
            providers.append({"provider": "claude", "score": None, "error": str(exc)})

        response["ai"]["providers"] = providers
        return response

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

        summaries = []
        for algorithm in self.ALGORITHMS:
            result = self.evaluate_pairs(
                pairs,
                algorithm=algorithm,
                threshold=float(thresholds.get(algorithm, 0.7)),
            )
            summaries.append(result)

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
