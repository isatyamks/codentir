from typing import Dict, List

from src.data.graph import GraphService


class HypothesisValidator:
    def __init__(self, graph_svc: GraphService):
        self.graph_svc = graph_svc

    def validate(self, issue_id: str, hypotheses: List[str]) -> Dict[str, float]:
        """
        Checks the hypotheses against the graph. If a hypothesis maps to a real graph node,
        we run a shortest_path calculation. The shorter the path, the higher the score.
        Returns a dict of {hypothesis: base_score}
        """
        scores = {}
        for h in hypotheses:
            scores[h] = 0.1  # Baseline

            # Try to find if this hypothesis corresponds to a real ID in the graph
            target_node = None
            for n in self.graph_svc.graph.nodes:
                if h in str(n):
                    target_node = n
                    break

            if target_node and issue_id:
                path = self.graph_svc.get_shortest_path(issue_id, target_node)
                if path:
                    # Score inversely proportional to path length (shorter is better)
                    length = len(path)
                    scores[h] = max(0.95 - (length * 0.1), 0.3)
                else:
                    scores[h] = 0.2  # Node exists but no path

        return scores
