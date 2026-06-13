from typing import List

from pydantic import BaseModel

# uncomment the corresponding imports below to avoid NameError:
# from .evidence_path import EvidencePath
# from .causal_candidate import CausalCandidate

class ImpactExplanation(BaseModel):
    entity_id: str
    reason: str
    graph_path: List[str]
    impact_score: float
