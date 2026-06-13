from pydantic import BaseModel

# uncomment the corresponding imports below to avoid NameError:
# from .benchmark_query import BenchmarkQuery
# from .benchmark_suite import BenchmarkSuite

class BenchmarkResult(BaseModel):
    query_id: str
    recall_at_k: float
    mrr: float
    ndcg: float
    latency_ms: float
