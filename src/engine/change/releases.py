from typing import Dict, List

from src.data.graph import GraphService


class ReleaseAnalyzer:
    def __init__(self, graph_svc: GraphService):
        self.graph_svc = graph_svc

    def analyze(self, release_id: str) -> Dict[str, List[str]]:
        """
        Identify all changes shipped in a deployment (Release -> PR -> Commit).
        """
        g = self.graph_svc.graph
        shipped_prs = []
        shipped_commits = []

        if release_id in g:
            import networkx as nx

            for n in nx.ancestors(g, release_id):
                n_data = g.nodes[n]
                ntype = n_data.get("type")
                if ntype in ["pull_request", "pullrequest"]:
                    shipped_prs.append(n)
                elif ntype == "commit":
                    shipped_commits.append(n)

        return {"shipped_prs": shipped_prs, "shipped_commits": shipped_commits}
