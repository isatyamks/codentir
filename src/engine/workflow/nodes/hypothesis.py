from src.engine.causal.generator import HypothesisGenerator
from src.engine.workflow.nodes.utils import print_phase
from src.engine.workflow.state import InvestigationState


def get_hypothesis_generation_node(hyp_gen: HypothesisGenerator):
    def _hypothesis_generation(state: InvestigationState):
        print_phase("Technical Explanation Generation")
        if not state["scored_candidates"]:
            return {"technical_explanation": "Could not determine a root cause from the graph evidence."}

        top_candidate = state["scored_candidates"][0]
        explanation = hyp_gen.generate(
            state["query"], top_candidate, state.get("human_feedback", [])
        )
        print(f"  \033[90mGenerated deterministic explanation.\033[0m")
        return {"technical_explanation": explanation}

    return _hypothesis_generation
