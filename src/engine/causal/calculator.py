from typing import List

from src.engine.causal.models import CausalCandidate, EvidencePath


class ConfidenceCalculator:
    def score_candidates(
        self, candidates: List[str], strongest_path: EvidencePath
    ) -> List[CausalCandidate]:
        """
        Calculates deterministic confidence breakdown without LLM hallucination.
        Scores each extracted graph candidate based on the strongest evidence path.
        """
        scored = []
        path_nodes = strongest_path.nodes

        for cand_id in candidates:
            # 1. Graph Support: Is it in the strongest path?
            graph_support = 0.95 if cand_id in path_nodes else 0.4

            # 2. Distance to Incident: Where does it appear in the path?
            distance_to_incident = 0.0
            if cand_id in path_nodes:
                idx = path_nodes.index(cand_id)
                # The earlier in the path, the closer to the incident (assuming path goes Incident -> ... -> Commit)
                distance_to_incident = max(0.9 - (idx * 0.1), 0.2)

            # 3. Temporal Correlation & Retrieval Relevance (simplified graph-based metrics)
            temporal_correlation = graph_support * 0.9
            evidence_completeness = strongest_path.score
            path_consistency = 0.95

            final_score = (
                (graph_support * 0.3)
                + (distance_to_incident * 0.2)
                + (temporal_correlation * 0.2)
                + (evidence_completeness * 0.15)
                + (path_consistency * 0.15)
            )

            reason = ""
            if cand_id in path_nodes:
                reason = "Appears on strongest causal path. "
                if idx == len(path_nodes) - 1:
                    reason += "Deepest root cause found in the chain."
            else:
                reason = "Extracted from secondary graph paths."

            scored.append(
                CausalCandidate(
                    candidate_id=cand_id,
                    score=round(final_score, 2),
                    reason=reason.strip(),
                    evidence_path=strongest_path,
                )
            )

        scored.sort(key=lambda x: x.score, reverse=True)
        return scored
