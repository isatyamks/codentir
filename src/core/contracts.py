"""
Core contracts (interfaces) for the codentir domain.
Flat file — replaces the old nested core/agents/*.py files.
"""

from abc import ABC, abstractmethod
from typing import List

from src.core.entities import Dataset


class SearchResult:
    """Value object returned by all retriever implementations."""

    def __init__(
        self,
        artifact_id: str,
        artifact_type: str,
        score: float,
        content: str,
        tenant_id: str = "tenant_default",
    ):
        self.artifact_id = artifact_id
        self.artifact_type = artifact_type
        self.score = score
        self.content = content
        self.tenant_id = tenant_id


class IRetriever(ABC):
    """Interface for a retrieval engine (Dense, Sparse, or Hybrid)."""

    @abstractmethod
    def index(self, dataset: Dataset) -> None:
        pass

    @abstractmethod
    def search(self, query: str, tenant_id: str, top_k: int = 10) -> List[SearchResult]:
        pass


class ICrossEncoderReranker(ABC):
    """Interface for reranking top-K results."""

    @abstractmethod
    def rerank(self, query: str, candidates: List[SearchResult]) -> List[SearchResult]:
        pass


class IDatasetReader(ABC):
    """Interface for loading generated data into domain aggregates."""

    @abstractmethod
    def load(self, base_path: str) -> Dataset:
        pass


class IGraphExporter(ABC):
    """Interface for exporting domain entities to graph structures."""

    @abstractmethod
    def export(self, dataset: Dataset, output_dir: str, tenant_id: str) -> None:
        pass
