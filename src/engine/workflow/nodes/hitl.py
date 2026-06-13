"""
Human-in-the-loop node — flattened from investigation/nodes/hitl/ + hitl/llm_interaction/.
"""

import json
import logging
from typing import List, Optional

import networkx as nx

from src.core.llm import AgentMessage, llmProvider
from src.data.graph import GraphService
from src.engine.workflow.nodes.utils import print_phase
from src.engine.workflow.state import InvestigationState

logger = logging.getLogger(__name__)


# ── helpers ───────────────────────────────────────────────────────────────────

def _get_target_id(state: InvestigationState, consulted_targets: List[str]) -> Optional[str]:
    for key in ["scored_candidates", "cause_candidates", "initial_artifacts"]:
        cands = state.get(key, [])
        for cand in cands:
            cand_id = cand.candidate_id if hasattr(cand, "candidate_id") else cand
            if cand_id not in consulted_targets:
                return cand_id
    return None


def _get_unique_stakeholders(graph_svc: GraphService, target_id: str):
    emps = []
    if target_id and target_id in graph_svc.graph:
        neighbors = nx.descendants(graph_svc.graph, target_id) | nx.ancestors(
            graph_svc.graph, target_id
        )
        for n in neighbors:
            nd = graph_svc.graph.nodes.get(n, {})
            if nd.get("type") == "employee":
                emps.append(nd.get("obj"))

    uniq = []
    seen = set()
    for e in emps:
        n = e.profile.get("firstName", "") + " " + e.profile.get("lastName", "")
        if n not in seen:
            seen.add(n)
            uniq.append(e)
    return uniq


def _generate_prompt(state, target_id, emps, f_list) -> str:
    e_str = "\n".join(
        [
            f"- {e.profile.get('firstName')} {e.profile.get('lastName')} ({e.profile.get('title')})"
            for e in emps
        ]
    )
    if not e_str:
        e_str = "No specific code owners found in the graph."
    f_str = "\n".join(f_list) if f_list else "None yet."

    return (
        "You are codentir, an autonomous debugging agent investigating an issue. You are chatting with engineers over Slack.\n"
        f"Incident Query: '{state['query']}'\n"
        f"Current Suspect Artifact: '{target_id}'\n"
        f"Available Stakeholders to chat with:\n{e_str}\n\n"
        f"Chat History / Feedback:\n{f_str}\n\n"
        "Decide the next step by outputting a JSON object. You must KEEP CHATTING and asking follow-up questions until you get a correct, concrete answer or a solid lead. DO NOT give up easily. Once you have a solid lead, you can RETRIEVE more data from the DB. If it's an absolute dead end, you can PROCEED to report generation.\n"
        "JSON Format:\n"
        "{\n"
        '  "ACTION": "ASK" | "RETRIEVE" | "PROCEED",\n'
        '  "TARGET": "[Employee Name]" (Required if ACTION is ASK. You can ask the same person again to dig deeper.),\n'
        '  "RATIONALE": "[Your internal thought process]",\n'
        '  "QUESTION": "[Your Slack message. Tone should be friendly, casual, like a coworker.]"\n'
        "}"
    )


def _query_llm_action(llm: llmProvider, prompt: str) -> dict:
    try:
        msg = llm.generate([AgentMessage(role="system", content=prompt)])
        resp = msg.content
        s = resp.find("{")
        e = resp.rfind("}") + 1
        if s != -1 and e != 0:
            return json.loads(resp[s:e])
        return {"ACTION": "PROCEED", "RATIONALE": "Parse err."}
    except Exception as e:
        return {"ACTION": "PROCEED", "RATIONALE": f"Err: {e}"}


# ── node factory ──────────────────────────────────────────────────────────────

def get_human_in_the_loop_node(llm: llmProvider, graph_svc: GraphService):
    def _human_in_the_loop(state: InvestigationState):
        print_phase("Expert Consultation (Autonomous Sub-Agent)")

        c_targets = state.get("consulted_targets", [])
        f_list = state.get("human_feedback", [])
        l_count = state.get("loop_count", 0) + 1

        t_id = _get_target_id(state, c_targets)
        if not t_id:
            print("  \033[91mAll top candidates have already been consulted. Proceeding to report.\033[0m")
            return {"next_action": "PROCEED", "expert_consulted": True, "loop_count": l_count}

        c_targets.append(t_id)
        print(f"  \033[93mAnalyzing Artifact: {t_id}\033[0m")

        emps = _get_unique_stakeholders(graph_svc, t_id)

        q_asked = 0
        while q_asked < 6:
            p = _generate_prompt(state, t_id, emps, f_list)
            data = _query_llm_action(llm, p)
            action = data.get("ACTION", "PROCEED")

            if action == "ASK":
                print(f"\n\033[90m[Agent Thoughts: {data.get('RATIONALE', '')}]\033[0m")
                print(f"\033[95m[HUMAN IN THE LOOP - Asking {data.get('TARGET', 'Unknown')}]\033[0m")
                print(f"\033[96m{data.get('QUESTION', '')}\033[0m")
                fb = input("\nYour Response: ")
                if fb.strip():
                    f_list.append(f"Feedback from {data.get('TARGET')} regarding {t_id}: {fb}")
                q_asked += 1
            elif action == "RETRIEVE":
                print(f"\n\033[90m[Agent Thoughts: {data.get('RATIONALE', '')}]\033[0m\n  \033[92mLoop back.\033[0m")
                return {
                    "human_feedback": f_list,
                    "cause_candidates": [],
                    "scored_candidates": [],
                    "evidence_paths": [],
                    "expert_consulted": True,
                    "loop_count": l_count,
                    "consulted_targets": c_targets,
                    "next_action": "RETRIEVE",
                }
            else:
                print(f"\n\033[90m[Agent Thoughts: {data.get('RATIONALE', '')}]\033[0m\n  \033[92mProceed.\033[0m")
                return {
                    "human_feedback": f_list,
                    "expert_consulted": True,
                    "loop_count": l_count,
                    "consulted_targets": c_targets,
                    "next_action": "PROCEED",
                }

        print("\n  \033[93mConsultation limit reached. Defaulting to RETRIEVE.\033[0m")
        return {
            "human_feedback": f_list,
            "cause_candidates": [],
            "scored_candidates": [],
            "evidence_paths": [],
            "expert_consulted": True,
            "loop_count": l_count,
            "consulted_targets": c_targets,
            "next_action": "RETRIEVE",
        }

    return _human_in_the_loop
