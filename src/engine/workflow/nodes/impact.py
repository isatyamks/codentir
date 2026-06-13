from src.engine.analysis.impact import ImpactService
from src.engine.workflow.nodes.utils import print_phase
from src.engine.workflow.state import InvestigationState


def get_impact_node(impact_svc: ImpactService):
    def _impact(state: InvestigationState):
        print_phase("Evidence-Backed Blast Radius")
        if not state["scored_candidates"]:
            return {"blast_radius": {}}

        top_candidate = state["scored_candidates"][0]
        blast = impact_svc.calculate_blast_radius(
            [top_candidate.candidate_id], state["tenant_id"]
        )

        total_impact = sum(len(items) for items in blast.values())
        print(f"  \033[91mFound {total_impact} affected entities via graph paths.\033[0m")
        return {"blast_radius": blast}

    return _impact
