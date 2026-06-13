from src.data.graph import GraphService
from src.engine.change.owners import CodeOwnerService
from src.engine.change.deployments import DeploymentAnalyzer
from src.engine.change.diffs import DiffAnalyzer
from src.engine.change.releases import ReleaseAnalyzer
from src.engine.workflow.nodes.utils import print_phase
from src.engine.workflow.state import InvestigationState


def get_change_node(
    graph_svc: GraphService,
    deploy_analyzer: DeploymentAnalyzer,
    release_analyzer: ReleaseAnalyzer,
    diff_analyzer: DiffAnalyzer,
    code_owner_svc: CodeOwnerService,
):
    def _extract_change(state: InvestigationState):
        print_phase("Change Detail Extraction")
        if not state["scored_candidates"]:
            return {"diff_data": {}, "owners": {}, "associated_changes": {}}

        top_candidate_obj = state["scored_candidates"][0]
        top_candidate = top_candidate_obj.candidate_id

        associated_changes = {}
        node_data = graph_svc.graph.nodes.get(top_candidate, {})
        ntype = node_data.get("type", "")

        actual_root_cause = top_candidate

        if ntype == "deployment":
            associated_changes = deploy_analyzer.analyze(top_candidate)
            print(f"  \033[90mDEBUG: Deployment associated_changes: {associated_changes}\033[0m")
            if associated_changes.get("commits"):
                actual_root_cause = associated_changes["commits"][0]
        elif ntype == "release":
            associated_changes = release_analyzer.analyze(top_candidate)
            if associated_changes.get("shipped_commits"):
                actual_root_cause = associated_changes["shipped_commits"][0]

        if actual_root_cause != top_candidate:
            print(f"  \033[93mElevated root cause from {top_candidate} to {actual_root_cause}\033[0m")
            top_candidate_obj.candidate_id = actual_root_cause
            if actual_root_cause not in top_candidate_obj.evidence_path.nodes:
                top_candidate_obj.evidence_path.nodes.append(actual_root_cause)
        else:
            print(f"  \033[91mDEBUG: actual_root_cause ({actual_root_cause}) == top_candidate ({top_candidate})\033[0m")

        diff_data = diff_analyzer.extract_diff(actual_root_cause)
        owners = code_owner_svc.extract_owners(actual_root_cause)

        return {
            "diff_data": diff_data,
            "owners": owners,
            "associated_changes": associated_changes,
        }

    return _extract_change
