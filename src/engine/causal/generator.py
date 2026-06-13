from typing import List

from src.core.llm import AgentMessage, llmProvider
from src.engine.causal.models import CausalCandidate


class HypothesisGenerator:
    def __init__(self, llm: llmProvider):
        self.llm = llm

    def generate(
        self,
        query: str,
        top_candidate: CausalCandidate,
        human_feedback: List[str] = None,
    ) -> str:
        """
        Given the user issue and the top scored causal candidate, provide a technical explanation.
        The LLM explains the evidence discovered, incorporating any human feedback provided.
        """
        prompt = (
            f"Given the user query: '{query}'\n"
            f"The deterministic Change Intelligence engine has identified the root cause change as: {top_candidate.candidate_id}\n"
            f"Reasoning: {top_candidate.reason}\n"
            f"Evidence Path: {' -> '.join(top_candidate.evidence_path.nodes)}\n"
        )

        if human_feedback:
            prompt += f"\nAdditionally, an employee provided the following manual context during the investigation:\n"
            for feedback in human_feedback:
                prompt += f'- "{feedback}"\n'
            prompt += "\nPlease ensure this manual context is smoothly woven into your explanation as definitive fact.\n"

        prompt += (
            "\nCRITICAL INSTRUCTION: You must NOT invent explanations. You may ONLY summarize the evidence provided above. "
            "Every single sentence you write MUST reference specific evidence (e.g., a specific commit ID, a specific file, a specific metric spike, a specific alert, or a specific incident). "
            "Write a brief, direct 'Technical Explanation'."
        )

        msg = self.llm.generate([AgentMessage(role="system", content=prompt)])
        return msg.content
