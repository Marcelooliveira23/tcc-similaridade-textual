from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class ComparisonResult:
    id: str
    created_at: str
    text_a: str
    text_b: str
    tfidf_cosine: float
    jaccard: float
    levenshtein_similarity: float

    @classmethod
    def build(
        cls,
        text_a: str,
        text_b: str,
        tfidf_cosine: float,
        jaccard: float,
        levenshtein_similarity: float,
    ) -> "ComparisonResult":
        return cls(
            id=str(uuid4()),
            created_at=datetime.now(timezone.utc).isoformat(),
            text_a=text_a,
            text_b=text_b,
            tfidf_cosine=round(tfidf_cosine, 6),
            jaccard=round(jaccard, 6),
            levenshtein_similarity=round(levenshtein_similarity, 6),
        )

    def to_dict(self) -> dict:
        return asdict(self)
