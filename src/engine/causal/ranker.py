from typing import List

from src.data.graph import GraphService
from src.engine.causal.extractor import CauseCandidateExtractor
from src.engine.causal.models import EvidencePath


class PathRanker:
    def __init__(self, graph_svc: GraphService):
        self.graph_svc = graph_svc
        self.extractor = CauseCandidateExtractor(graph_svc)

    def rank_paths(self, paths: List[EvidencePath]) -> List[EvidencePath]:
        """
        Ranks paths based on how many valid causal nodes they contain,
        their length, and evidence density.
        """
        for path in paths:
            # 1. Base Score
            score = 0.5

            # 2. Extract causal candidates directly from this path
            # Need to wrap path in a list because extract_candidates takes List[EvidencePath]
            candidates = self.extractor.extract_candidates([path])

            # 3. Increase score based on the presence of causal candidates
            if candidates:
                score += min(
                    len(candidates) * 0.15, 0.4
                )  # Up to 0.4 points for having valid causes

            # 4. Reward traversing depends_on edges (cascading failure indicator)
            for i in range(len(path.nodes) - 1):
                n1, n2 = path.nodes[i], path.nodes[i + 1]
                edge_data = self.graph_svc.graph.get_edge_data(
                    n1, n2
                ) or self.graph_svc.graph.get_edge_data(n2, n1)
                if edge_data and edge_data.get("type") == "depends_on":
                    score += 0.05

            # 5. Ensure valid range
            path.score = max(min(score, 1.0), 0.1)

        # Sort highest score first
        paths.sort(key=lambda p: p.score, reverse=True)
        return paths
