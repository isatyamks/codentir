from langgraph.graph import END, StateGraph

from src.engine.workflow.state import InvestigationState


def build_workflow(self_obj):
    wf = StateGraph(InvestigationState)

    from src.engine.workflow.nodes.evidence import (
        get_cause_candidate_extraction_node,
        get_evidence_chain_discovery_node,
    )
    from src.engine.workflow.nodes.ranking import (
        get_change_ranking_node,
        get_path_ranking_node,
    )
    from src.engine.workflow.nodes.understand import get_understand_node
    from src.engine.workflow.nodes.retrieval import get_retrieval_node
    from src.engine.workflow.nodes.change import get_change_node
    from src.engine.workflow.nodes.hypothesis import get_hypothesis_generation_node
    from src.engine.workflow.nodes.impact import get_impact_node
    from src.engine.workflow.nodes.action import get_action_generation_node
    from src.engine.workflow.nodes.report import get_report_node
    from src.engine.workflow.nodes.qa import get_qa_node
    from src.engine.workflow.nodes.hitl import get_human_in_the_loop_node

    wf.add_node("understand", get_understand_node(self_obj.llm))
    wf.add_node(
        "initial_retrieval",
        get_retrieval_node(self_obj.retrieval_svc, self_obj.graph_svc),
    )
    wf.add_node(
        "evidence_chain_discovery", get_evidence_chain_discovery_node(self_obj.ev_chain)
    )
    wf.add_node("path_ranking", get_path_ranking_node(self_obj.path_ranker))
    wf.add_node(
        "cause_candidate_extraction",
        get_cause_candidate_extraction_node(self_obj.candidate_extractor),
    )
    wf.add_node("change_ranking", get_change_ranking_node(self_obj.change_ranker))
    wf.add_node(
        "extract_change",
        get_change_node(
            self_obj.graph_svc,
            self_obj.deploy_analyzer,
            self_obj.release_analyzer,
            self_obj.diff_analyzer,
            self_obj.code_owner_svc,
        ),
    )
    wf.add_node(
        "hypothesis_generation", get_hypothesis_generation_node(self_obj.hyp_gen)
    )
    wf.add_node("impact", get_impact_node(self_obj.impact_svc))
    wf.add_node(
        "action_generation",
        get_action_generation_node(self_obj.llm, self_obj.graph_svc),
    )
    wf.add_node("report", get_report_node())
    wf.add_node(
        "qa_generation", get_qa_node(self_obj.llm, self_obj.graph_svc)
    )
    wf.add_node(
        "human_in_the_loop",
        get_human_in_the_loop_node(self_obj.llm, self_obj.graph_svc),
    )

    wf.set_entry_point("understand")
    wf.add_edge("understand", "initial_retrieval")

    def route_after_ret(s):
        return (
            "qa_generation"
            if s.get("intent") == "GENERAL_QA"
            else "evidence_chain_discovery"
        )

    wf.add_conditional_edges(
        "initial_retrieval",
        route_after_ret,
        {
            "evidence_chain_discovery": "evidence_chain_discovery",
            "qa_generation": "qa_generation",
        },
    )
    wf.add_edge("qa_generation", END)
    wf.add_edge("evidence_chain_discovery", "path_ranking")
    wf.add_edge("path_ranking", "cause_candidate_extraction")
    wf.add_edge("cause_candidate_extraction", "change_ranking")

    def route_after_sc(s):
        if (
            not s.get("expert_consulted")
            or (not s.get("scored_candidates") and s.get("loop_count", 0) < 3)
            or (
                s.get("scored_candidates")
                and s["scored_candidates"][0].score <= 0.90
                and s.get("loop_count", 0) < 3
            )
        ):
            return "human_in_the_loop"
        return "extract_change"

    wf.add_conditional_edges(
        "change_ranking",
        route_after_sc,
        {
            "human_in_the_loop": "human_in_the_loop",
            "extract_change": "extract_change",
        },
    )

    def route_after_hitl(s):
        return (
            "extract_change"
            if s.get("next_action") == "PROCEED"
            else "initial_retrieval"
        )

    wf.add_conditional_edges(
        "human_in_the_loop",
        route_after_hitl,
        {
            "initial_retrieval": "initial_retrieval",
            "extract_change": "extract_change",
        },
    )

    wf.add_edge("extract_change", "hypothesis_generation")
    wf.add_edge("hypothesis_generation", "impact")
    wf.add_edge("impact", "action_generation")
    wf.add_edge("action_generation", "report")
    wf.add_edge("report", END)

    return wf.compile()
