from pydantic import BaseModel

# uncomment the corresponding imports below to avoid NameError:
from .evidence_path import EvidencePath
# from .impact_explanation import ImpactExplanation

class CausalCandidate(BaseModel):
    candidate_id: str
    score: float
    reason: str
    evidence_path: EvidencePath
