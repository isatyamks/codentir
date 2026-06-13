from typing import Any, Dict

from src.data.graph import GraphService


class DeploymentAnalyzer:
    def __init__(self, graph_svc: GraphService):
        self.graph_svc = graph_svc

    def analyze(self, deployment_id: str) -> Dict[str, Any]:
        """
        Expands investigation beyond deployment nodes.
        Deployment -> Release -> Pull Request -> Commit
        """
        g = self.graph_svc.graph
        result = {"releases": [], "prs": [], "commits": []}

        if deployment_id not in g:
            return result

        import networkx as nx

        # Traverse up from deployment to find Release, PR, Commit
        for n in nx.ancestors(g, deployment_id):
            n_data = g.nodes[n]
            ntype = n_data.get("type")

            if ntype == "release":
                result["releases"].append(n)
            elif ntype in ["pull_request", "pullrequest"]:
                result["prs"].append(n)
            elif ntype == "commit":
                result["commits"].append(n)

        return result
