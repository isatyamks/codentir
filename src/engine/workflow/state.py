from typing import Any, Dict, List, TypedDict


class InvestigationState(TypedDict):
    query: str
    tenant_id: str
    intent: str
    understanding: str
    initial_artifacts: List[str]
    expanded_artifacts: List[str]
    evidence_paths: List[Any]   # EvidencePath
    cause_candidates: List[str]
    scored_candidates: List[Any]  # CausalCandidate
    diff_data: Dict[str, Any]
    owners: Dict[str, str]
    associated_changes: Dict[str, Any]
    technical_explanation: str
    blast_radius: Dict[str, List[Any]]  # ImpactExplanation
    action_items: List[Dict[str, str]]
    human_feedback: List[str]
    report: str
    final_response: str
    loop_count: int
    expert_consulted: bool
    consulted_targets: List[str]
    next_action: str
