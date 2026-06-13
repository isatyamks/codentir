import logging

logger = logging.getLogger(__name__)

from typing import Any, Dict, List, Optional

from src.config.prompt import SYSTEM_PROMPT
from src.engine.generate.formatter import OutputFormatter


class UseCaseGenerator:

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()
        self.formatter = OutputFormatter()

    def generate(
        self, query: str, context_chunks: List[Dict[str, Any]], avg_score: float = 0.0
    ) -> Dict[str, Any]:

        try:
            with timer("use_case_generation"):
                context_text = self._format_context(context_chunks)

                prompt = get_generation_prompt(
                    query=query,
                    mode="use_case",
                    context_chunks=context_text,
                    avg_score=avg_score,
                )

                response = self.llm_client.generate(
                    prompt=prompt, system_prompt=SYSTEM_PROMPT, temperature=0.7
                )

                parsed = self.formatter.parse_json_response(response["content"])

                if not parsed:
                    return self.formatter.create_error_response(
                        query=query,
                        error_type="parse_error",
                        message="Failed to parse LLM response as JSON",
                    )

                if not self.formatter.validate_use_case(parsed):
                    pass

                formatted = self.formatter.format_use_case(parsed)

                formatted["tokens"] = response.get("tokens", {})
                formatted["model"] = response.get("model", "")
                formatted["success"] = True

                return formatted

        except Exception as e:
            return self.formatter.create_error_response(
                query=query, error_type="generation_error", message=str(e)
            )

    def _format_context(self, chunks: List[Dict[str, Any]]) -> str:
        if not chunks:
            return "No context available."

        formatted = []
        for i, chunk in enumerate(chunks, 1):
            score = chunk.get("hybrid_score", chunk.get("similarity", 0))
            content = chunk.get("content", "")
            source = chunk.get("metadata", {}).get("file_name", "unknown")

            formatted.append(
                f"[Chunk {i}] (Score: {score:.3f}, Source: {source})\n{content}\n"
            )

        return "\n---\n".join(formatted)
