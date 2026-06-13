"""
Ranking nodes — flattened from investigation/nodes/ranking/*.py
"""

from src.engine.causal.ranker import PathRanker
from src.engine.change.ranker import ChangeRanker
from src.engine.workflow.nodes.utils import print_phase
from src.engine.workflow.state import InvestigationState


def get_path_ranking_node(path_ranker: PathRanker):
    def _path_ranking(state: InvestigationState):
        print_phase("Path Ranking")
        ranked_paths = path_ranker.rank_paths(state["evidence_paths"])
        if ranked_paths:
            print(f"  \033[92mStrongest path score: {ranked_paths[0].score:.2f}\033[0m")
        return {"evidence_paths": ranked_paths}

    return _path_ranking


def get_change_ranking_node(change_ranker: ChangeRanker):
    def _change_ranking(state: InvestigationState):
        print_phase("Change Intelligence Ranking")
        if not state.get("evidence_paths") or not state.get("cause_candidates"):
            print("  \033[91mNo evidence paths or candidates found.\033[0m")
            return state

        print("\n\033[94m[Change Ranking & Correlation]\033[0m")
        all_scored_candidates = []
        for path in state["evidence_paths"][:5]:
            scored = change_ranker.rank_candidates(state["cause_candidates"], path)
            all_scored_candidates.extend(scored)

        all_scored_candidates.sort(key=lambda x: x.score, reverse=True)

        seen = set()
        scored_candidates = []
        for cand in all_scored_candidates:
            if cand.candidate_id not in seen:
                seen.add(cand.candidate_id)
                scored_candidates.append(cand)

        state["scored_candidates"] = scored_candidates
        return state

    return _change_ranking
