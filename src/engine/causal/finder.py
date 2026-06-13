from typing import List

from src.data.graph import GraphService


class CausalPathFinder:
    def __init__(self, graph_svc: GraphService):
        self.graph_svc = graph_svc

    def find_paths(self, issue_id: str, potential_causes: List[str]) -> List[List[str]]:
        """
        Searches the graph for shortest paths connecting the User Issue to Potential Causes.
        """
        paths = []
        for cause in potential_causes:
            p = self.graph_svc.get_shortest_path(issue_id, cause)
            if p:
                paths.append(p)

        # Sort by shortest path first (strongest direct causal link)
        paths.sort(key=len)
        return paths
