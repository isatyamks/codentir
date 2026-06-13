from typing import List

from pydantic import BaseModel

# uncomment the corresponding imports below to avoid NameError:
# from .benchmark_query import BenchmarkQuery
# from .benchmark_result import BenchmarkResult

class BenchmarkSuite(BaseModel):
    name: str
    description: str
    queries: List[BenchmarkQuery]
