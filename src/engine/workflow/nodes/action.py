import networkx as nx

from src.core.llm import AgentMessage, llmProvider
from src.data.graph import GraphService
from src.engine.workflow.nodes.utils import print_phase
from src.engine.workflow.state import InvestigationState


def get_action_generation_node(llm: llmProvider, graph_svc: GraphService):
    def _action_generation(state: InvestigationState):
        print_phase("Action Plan & Responsible Personnel")
        action_items = []
        if not state["scored_candidates"]:
            return {"action_items": []}

        top_candidate = state["scored_candidates"][0].candidate_id

        responsible_employees = []
        if top_candidate in graph_svc.graph:
            neighbors = nx.descendants(graph_svc.graph, top_candidate) | nx.ancestors(
                graph_svc.graph, top_candidate
            )
            for n in neighbors:
                node_data = graph_svc.graph.nodes.get(n, {})
                if node_data.get("type") == "employee":
                    responsible_employees.append(node_data.get("obj"))

        responsible_employees = responsible_employees[:3]

        if not responsible_employees:
            return {"action_items": []}

        for emp in responsible_employees:
            name = (
                emp.profile.get("firstName", "Employee")
                + " "
                + emp.profile.get("lastName", "")
            )
            role = emp.profile.get("title", "Engineer")

            prompt = (
                f"Incident Root Cause: {top_candidate}\n"
                f"Technical Explanation:\n{state['technical_explanation']}\n\n"
                f"Employee Name: {name}\n"
                f"Employee Role: {role}\n\n"
                "Please write a short, direct message (1 paragraph) to this employee. "
                "Explain why they are being notified, how this incident connects to their role, "
                "and provide 2-3 specific, actionable steps they must take to resolve or mitigate the issue."
            )
            msg = llm.generate([AgentMessage(role="system", content=prompt)])
            action_items.append(
                {"employee_name": name, "role": role, "suggestion": msg.content}
            )

        return {"action_items": action_items}

    return _action_generation
