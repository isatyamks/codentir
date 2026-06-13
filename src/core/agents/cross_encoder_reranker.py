from abc import ABC, abstractmethod
from typing import List

# uncomment the corresponding imports below to avoid NameError:
# from .i_generator_reader import IgeneratorReader
from .search_result import SearchResult
# from .i_retriever import IRetriever
# from .i_graph_exporter import IGraphExporter


class ICrossEncoderReranker(ABC):
    """Interface for reranking top K results."""

    @abstractmethod
    def rerank(self, query: str, candidates: List[SearchResult]) -> List[SearchResult]:
        pass
