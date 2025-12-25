from typing import Dict, Any, List, Optional

from src.generation.llm_client import LLMClient
from src.generation.output_formatter import OutputFormatter
from src.config import get_generation_prompt, SYSTEM_PROMPT
from src.utils import get_logger, timer

logger = get_logger(__name__)


class UseCaseGenerator:
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()
        self.formatter = OutputFormatter()
        logger.info("UseCaseGenerator initialized")
    
    def generate(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        avg_score: float = 0.0
    ) -> Dict[str, Any]:
    
        logger.info(f"Generating use case for query: '{query}'")
        
        try:
            with timer("use_case_generation"):
                context_text = self._format_context(context_chunks)
                
                prompt = get_generation_prompt(
                    query=query,
                    mode="use_case",
                    context_chunks=context_text,
                    avg_score=avg_score
                )
                
                response = self.llm_client.generate(
                    prompt=prompt,
                    system_prompt=SYSTEM_PROMPT,
                    temperature=0.7
                )
                
                parsed = self.formatter.parse_json_response(response["content"])
                
                if not parsed:
                    logger.error("Failed to parse use case response")
                    return self.formatter.create_error_response(
                        query=query,
                        error_type="parse_error",
                        message="Failed to parse LLM response as JSON"
                    )
                
                if not self.formatter.validate_use_case(parsed):
                    logger.warning("Use case validation failed, attempting to fix")
                
                formatted = self.formatter.format_use_case(parsed)
                
                formatted["tokens"] = response.get("tokens", {})
                formatted["model"] = response.get("model", "")
                formatted["success"] = True
                
                logger.info("Use case generated successfully")
                return formatted
        
        except Exception as e:
            logger.error(f"Use case generation failed: {e}")
            return self.formatter.create_error_response(
                query=query,
                error_type="generation_error",
                message=str(e)
            )
    
    def _format_context(self, chunks: List[Dict[str, Any]]) -> str:
        if not chunks:
            return "No context available."
        
        formatted = []
        for i, chunk in enumerate(chunks, 1):
            score = chunk.get('hybrid_score', chunk.get('similarity', 0))
            content = chunk.get('content', '')
            source = chunk.get('metadata', {}).get('file_name', 'unknown')
            
            formatted.append(
                f"[Chunk {i}] (Score: {score:.3f}, Source: {source})\n{content}\n"
            )
        
        return "\n---\n".join(formatted)
