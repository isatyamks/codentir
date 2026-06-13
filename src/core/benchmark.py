"""
Benchmark models — flattened from core/benchmark/*.py.
"""

from typing import List

from pydantic import BaseModel


class BenchmarkQuery(BaseModel):
    query_id: str
    query_text: str
    category: str
    expected_documents: List[str]


class BenchmarkResult(BaseModel):
    query_id: str
    recall_at_k: float
    mrr: float
    ndcg: float
    latency_ms: float


class BenchmarkSuite(BaseModel):
    name: str
    description: str
    queries: List[BenchmarkQuery]
