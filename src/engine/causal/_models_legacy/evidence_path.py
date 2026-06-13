from typing import List

from pydantic import BaseModel

# uncomment the corresponding imports below to avoid NameError:
# from .causal_candidate import CausalCandidate
# from .impact_explanation import ImpactExplanation

class EvidencePath(BaseModel):
    nodes: List[str]
    score: float = 0.0
    path_type: str = "unknown"
