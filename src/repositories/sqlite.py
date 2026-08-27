import os
import sqlite3

from src.models.comparison import ComparisonResult
from src.repositories.base import ComparisonRepository


class SQLiteComparisonRepository(ComparisonRepository):
    def __init__(self, database_path: str) -> None:
        if database_path != ":memory:":
            os.makedirs(os.path.dirname(database_path) or ".", exist_ok=True)

        self._conn = sqlite3.connect(database_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS comparisons (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                text_a TEXT NOT NULL,
                text_b TEXT NOT NULL,
                tfidf_cosine REAL NOT NULL,
                jaccard REAL NOT NULL,
                levenshtein_similarity REAL NOT NULL
            )
            """
        )
        self._conn.commit()

    def save(self, comparison: ComparisonResult) -> None:
        self._conn.execute(
            """
            INSERT INTO comparisons (
                id,
                created_at,
                text_a,
                text_b,
                tfidf_cosine,
                jaccard,
                levenshtein_similarity
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                comparison.id,
                comparison.created_at,
                comparison.text_a,
                comparison.text_b,
                comparison.tfidf_cosine,
                comparison.jaccard,
                comparison.levenshtein_similarity,
            ),
        )
        self._conn.commit()

    def list_all(self) -> list[ComparisonResult]:
        rows = self._conn.execute(
            """
            SELECT
                id,
                created_at,
                text_a,
                text_b,
                tfidf_cosine,
                jaccard,
                levenshtein_similarity
            FROM comparisons
            ORDER BY created_at DESC
            """
        ).fetchall()

        return [
            ComparisonResult(
                id=row["id"],
                created_at=row["created_at"],
                text_a=row["text_a"],
                text_b=row["text_b"],
                tfidf_cosine=row["tfidf_cosine"],
                jaccard=row["jaccard"],
                levenshtein_similarity=row["levenshtein_similarity"],
            )
            for row in rows
        ]

    def close(self) -> None:
        self._conn.close()
