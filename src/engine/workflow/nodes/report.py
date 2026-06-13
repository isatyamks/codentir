"""
Report node — flattened from investigation/nodes/report.py + nodes/report_utils/*.py
"""

import json
import logging
import os
from datetime import datetime

from src.engine.workflow.nodes.utils import print_phase
from src.engine.workflow.state import InvestigationState

logger = logging.getLogger(__name__)


# ── helpers ───────────────────────────────────────────────────────────────────

def _format_report(state, top_cand, s_path):
    d = state.get("diff_data", {})
    ow = state.get("owners", {})
    r = [f"Issue: {state['query']}\n\nSelected Root Cause: {top_cand.candidate_id}"]
    if ow.get("Commit Author"):
        r.append(f"Author: {ow.get('Commit Author')}")

    p_id, d_id = None, None
    for n in s_path.nodes:
        if "PR-" in n or "pullrequest" in n.lower():
            p_id = n
        elif "DEPLOY-" in n or "deployment" in n.lower():
            d_id = n

    if p_id:
        r.append(f"PR: {p_id}")
    if d_id:
        r.append(f"Deployment: {d_id}")
    if d.get("files_changed"):
        r.append(f"Changed Files: {', '.join(d['files_changed'])}")
    if d.get("diff_summary"):
        r.append(f"Change Introduced: {d['diff_summary']}")

    r.append("\nEvidence Chain (Chronological Events):")
    f_path = [f"[{i+1}] {node}" for i, node in enumerate(s_path.nodes)]
    r.append(" ->\n  ".join(f_path))
    r.append("\nThis sequence perfectly maps the action taken causing the final issue with over 90% confidence.\n")

    r.append("Technical Explanation:\n" + state["technical_explanation"] + "\n")

    r.append("Confidence:")
    res = top_cand.reason
    if "(" in res:
        pts = res.split("(", 1)[1].replace(")", "").split(", ")
        r.extend(pts)
        r.append(res.split(" (")[0])
    else:
        r.append(f"Final Confidence: {top_cand.score:.2f}")

    r.append("\nBlast Radius:")
    for cat, expls in state["blast_radius"].items():
        if expls:
            r.append(f"[{cat}]")
            r.extend([f"- {ex.entity_id} (Reason: {ex.reason})" for ex in expls])
            r.append("")

    r.append("Responsible Personnel:")
    r.extend([f"{rl}: {nm}" for rl, nm in ow.items() if nm])
    r.append("")

    if state.get("action_items"):
        r.append("Recommended Actions:")
        for a in state["action_items"]:
            r.extend([f"@{a['employee_name']} ({a['role']})", f"{a['suggestion']}\n"])

    return "\n".join(r), f_path


def _save_postmortem(state, top_cand, path_list):
    t_id = state.get("tenant_id", "default")
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    pm_id = f"AUTO-PM-{ts}"
    pm_data = {
        "id": pm_id,
        "incident_id": "AUTO-INVESTIGATION",
        "title": f"Investigation Report: {state['query']}",
        "content": "Full Chat History:\n" + "\n".join(state.get("human_feedback", [])),
        "root_cause_summary": f"Selected Root Cause: {top_cand.candidate_id}\n\nTechnical Explanation:\n{state['technical_explanation']}",
        "lessons_learned": "Action Plan:\n"
        + "\n".join([f"@{a['employee_name']}: {a['suggestion']}" for a in state.get("action_items", [])]),
        "created_at": datetime.now().isoformat(),
        "investigation_data": {"evidence_chain": path_list},
    }

    dir_p = os.path.join("data", t_id, "postmortems")
    os.makedirs(dir_p, exist_ok=True)
    p = os.path.join(dir_p, f"{pm_id}.json")
    try:
        with open(p, "w") as f:
            json.dump(pm_data, f, indent=2)
        print(f"  \033[92mSaved memory to {p}\033[0m")
    except Exception as e:
        print(f"  \033[91mFailed to save: {e}\033[0m")


# ── node factory ──────────────────────────────────────────────────────────────

def get_report_node():
    def _report(state: InvestigationState):
        print_phase("Report Generation")

        if not state["scored_candidates"] or not state["evidence_paths"]:
            r = "Investigation failed to uncover causal evidence paths."
            return {"report": r, "final_response": r}

        tc = state["scored_candidates"][0]
        sp = tc.evidence_path

        rep_str, f_path = _format_report(state, tc, sp)
        _save_postmortem(state, tc, f_path)

        return {"report": rep_str, "final_response": rep_str}

    return _report
