from typing import List

from pydantic import BaseModel

# uncomment the corresponding imports below to avoid NameError:
# from .benchmark_suite import BenchmarkSuite
# from .benchmark_result import BenchmarkResult

class BenchmarkQuery(BaseModel):
    query_id: str
    query_text: str
    category: str
    expected_documents: List[str]
