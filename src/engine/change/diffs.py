from typing import Any, Dict

from src.data.graph import GraphService


class DiffAnalyzer:
    def __init__(self, graph_svc: GraphService):
        self.graph_svc = graph_svc

    def extract_diff(self, commit_id: str) -> Dict[str, Any]:
        """
        Extract actual technical changes.
        """
        g = self.graph_svc.graph
        if commit_id not in g:
            return {"files_changed": [], "diff_summary": "No diff found."}

        node_data = g.nodes[commit_id]
        obj = node_data.get("obj")

        if not obj:
            return {"files_changed": [], "diff_summary": "No diff found."}

        return {
            "files_changed": getattr(obj, "files_changed", []),
            "diff_summary": getattr(obj, "diff_summary", "No diff summary available."),
        }
