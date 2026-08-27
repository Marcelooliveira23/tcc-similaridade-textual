from src.models.comparison import ComparisonResult
from src.repositories.base import ComparisonRepository


class InMemoryComparisonRepository(ComparisonRepository):
    def __init__(self) -> None:
        self._items: list[ComparisonResult] = []

    def save(self, comparison: ComparisonResult) -> None:
        self._items.append(comparison)

    def list_all(self) -> list[ComparisonResult]:
        return list(self._items)
