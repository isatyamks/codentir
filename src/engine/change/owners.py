from typing import Any, Dict

import networkx as nx

from src.data.graph import GraphService


class CodeOwnerService:
    def __init__(self, graph_svc: GraphService):
        self.graph_svc = graph_svc

    def extract_owners(self, commit_id: str) -> Dict[str, Any]:
        """
        Finds Commit Author, PR Reviewer, Service Owner, Deployment Approver using the graph.
        """
        g = self.graph_svc.graph
        owners = {"Commit Author": None, "Service Owner": None}

        if commit_id not in g:
            return owners

        commit_node = g.nodes[commit_id]
        obj = commit_node.get("obj")
        if obj and hasattr(obj, "author_name"):
            owners["Commit Author"] = obj.author_name

        # Find Service Owner by traversing Commit -> PR -> Release -> Deployment -> Service -> Team
        neighbors = nx.ancestors(g, commit_id) | nx.descendants(g, commit_id)
        for n in neighbors:
            n_data = g.nodes[n]
            if n_data.get("type") == "team":
                team_obj = n_data.get("obj")
                if team_obj:
                    owners["Service Owner"] = team_obj.name
                    break

        return owners
