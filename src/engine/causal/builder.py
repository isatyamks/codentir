from typing import List

from src.data.graph import GraphService
from src.engine.causal.models import EvidencePath


class EvidenceChainBuilder:
    def __init__(self, graph_svc: GraphService):
        self.graph_svc = graph_svc

    def build_chains(self, artifacts: List[str]) -> List[EvidencePath]:
        """
        Builds deterministic evidence chains from the expanded artifacts.
        Finds multiple paths between observational nodes and other elements.
        """
        chains = []

        # We find paths from observational evidence (incidents, alerts, metrics, logs, etc) to other entities
        observations = [
            a
            for a in artifacts
            if any(
                prefix in a
                for prefix in ["INC-", "ALERT-", "METRIC-", "LOG-", "SLACK-"]
            )
        ]

        # We want to find paths from any observation to any candidate or other observation
        for obs_id in observations:
            for target_id in artifacts:
                if obs_id == target_id:
                    continue
                path = self.graph_svc.get_shortest_path(obs_id, target_id)
                if path and len(path) > 1:
                    # Build EvidencePath
                    ep = EvidencePath(
                        nodes=path,
                        score=0.0,  # Handled later by PathRanker
                        path_type="observational_to_target",
                    )
                    chains.append(ep)

        return chains

    def format_chain(self, chain: EvidencePath) -> str:
        clean_chain = [c.split("::")[-1] for c in chain.nodes]
        return "\n↓\n".join(clean_chain)
