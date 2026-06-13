from typing import Any, Dict, List

from src.data.graph import GraphService


class CommitAnalyzer:
    def __init__(self, graph_svc: GraphService):
        self.graph_svc = graph_svc

    def analyze(self, commit_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Identify candidate commits features (ticket linkage, service linkage, temporal proximity).
        """
        g = self.graph_svc.graph
        results = []

        for cid in commit_ids:
            if cid not in g:
                continue

            node_data = g.nodes[cid]
            obj = node_data.get("obj")

            features = {
                "id": cid,
                "message": getattr(obj, "message", ""),
                "author": getattr(obj, "author_name", ""),
                "linked_tickets": [],
                "linked_services": [],
            }

            # Find tickets
            for neighbor in g.neighbors(cid):
                n_data = g.nodes[neighbor]
                if n_data.get("type") == "ticket":
                    features["linked_tickets"].append(neighbor)
                elif n_data.get("type") == "service":
                    features["linked_services"].append(neighbor)

            results.append(features)

        return results
