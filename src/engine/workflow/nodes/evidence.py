"""
Evidence nodes — flattened from investigation/nodes/evidence/*.py
"""

from src.engine.causal.extractor import CauseCandidateExtractor
from src.engine.causal.builder import EvidenceChainBuilder
from src.engine.workflow.nodes.utils import print_phase
from src.engine.workflow.state import InvestigationState


def get_evidence_chain_discovery_node(ev_chain: EvidenceChainBuilder):
    def _evidence_chain_discovery(state: InvestigationState):
        print_phase("Evidence Chain Discovery")
        paths = ev_chain.build_chains(state["expanded_artifacts"])
        print(f"  \033[92mFound {len(paths)} raw evidence paths.\033[0m")
        return {"evidence_paths": paths}

    return _evidence_chain_discovery


def get_cause_candidate_extraction_node(candidate_extractor: CauseCandidateExtractor):
    def _cause_candidate_extraction(state: InvestigationState):
        print_phase("Cause Candidate Extraction")
        candidates = candidate_extractor.extract_candidates(state["evidence_paths"])
        print(f"  \033[93mExtracted {len(candidates)} valid causal candidates.\033[0m")
        return {"cause_candidates": candidates}

    return _cause_candidate_extraction
