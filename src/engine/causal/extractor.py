from typing import List, Set

from src.data.graph import GraphService
from src.engine.causal.models import EvidencePath


class CauseCandidateExtractor:
    VALID_CAUSE_TYPES: Set[str] = {
        "Commit",
        "PullRequest",
        "Release",
        "Deployment",
        "ConfigChange",
        "FeatureFlag",
        "InfrastructureChange",
        "commit",
        "pullrequest",
        "release",
        "deployment",
        "configchange",
        "featureflag",
        "infrastructurechange",
    }

    INVALID_CAUSE_TYPES: Set[str] = {
        "Incident",
        "Alert",
        "Metric",
        "Log",
        "Service",
        "SlackMessage",
        "Postmortem",
        "incident",
        "alert",
        "metric",
        "log",
        "service",
        "slackmessage",
        "postmortem",
    }

    def __init__(self, graph_svc: GraphService):
        self.graph_svc = graph_svc

    def extract_candidates(self, evidence_paths: List["EvidencePath"]) -> List[str]:
        """
        Traverses evidence paths and extracts only valid causal entities.
        Ignores observational entities like Incidents and Alerts.
        """
        candidates = set()

        for path in evidence_paths:
            for node_id in path.nodes:
                # Retrieve node data from the graph
                node_data = self.graph_svc.get_node(node_id)
                if not node_data:
                    continue

                node_label = node_data.get("label", "").lower()
                node_type = node_data.get("type", "").lower()

                # Check if it matches any valid type (case-insensitive check against sets)
                is_valid = any(
                    valid_type.lower() in node_label or valid_type.lower() in node_type
                    for valid_type in self.VALID_CAUSE_TYPES
                )

                is_invalid = any(
                    invalid_type.lower() in node_label
                    or invalid_type.lower() in node_type
                    for invalid_type in self.INVALID_CAUSE_TYPES
                )

                if is_valid and not is_invalid:
                    candidates.add(node_id)

        return list(candidates)
