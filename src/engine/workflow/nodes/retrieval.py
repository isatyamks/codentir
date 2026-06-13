from src.data.graph import GraphService
from src.data.retrieval import RetrievalService
from src.engine.workflow.nodes.utils import print_phase
from src.engine.workflow.state import InvestigationState


def get_retrieval_node(retrieval_svc: RetrievalService, graph_svc: GraphService):
    def _initial_retrieval(state: InvestigationState):
        print_phase("Initial Evidence Gathering")

        search_query = state["query"]
        if state.get("human_feedback"):
            print("  \033[93mEnriching search query with human feedback...\033[0m")
            search_query += " " + " ".join(state["human_feedback"])

        results = retrieval_svc.initial_retrieval(search_query, state["tenant_id"])
        ids = [r.artifact_id for r in results]

        expanded = graph_svc.iterative_expansion(ids, state["tenant_id"], max_depth=10)
        all_artifacts = list(set(ids + list(expanded)))

        print(f"  \033[92mDiscovered {len(all_artifacts)} relevant artifacts.\033[0m")
        return {"initial_artifacts": ids, "expanded_artifacts": all_artifacts}

    return _initial_retrieval
