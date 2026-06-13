"""
Causal reasoning models — flattened from engine/causal/models/*.py.
"""

from typing import List

from pydantic import BaseModel


class EvidencePath(BaseModel):
    nodes: List[str]
    score: float = 0.0
    path_type: str = "unknown"


class CausalCandidate(BaseModel):
    candidate_id: str
    score: float
    reason: str
    evidence_path: EvidencePath


class ImpactExplanation(BaseModel):
    entity_id: str
    reason: str
    graph_path: List[str]
    impact_score: float
