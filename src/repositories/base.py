from abc import ABC, abstractmethod

from src.models.comparison import ComparisonResult


class ComparisonRepository(ABC):
    @abstractmethod
    def save(self, comparison: ComparisonResult) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> list[ComparisonResult]:
        raise NotImplementedError
