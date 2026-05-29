from typing import Dict, Any, List, Optional

from src.generation.llm_client import LLMClient
from src.generation.output_formatter import OutputFormatter
from src.config import get_generation_prompt, SYSTEM_PROMPT
from src.utils import timer


class TestCaseGenerator:
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()
        self.formatter = OutputFormatter()
    
    def generate(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        avg_score: float = 0.0,
        min_positive: int = 3,
        min_negative: int = 2,
        min_boundary: int = 2
    ) -> Dict[str, Any]:
       
        try:
            with timer("test_case_generation"):
                context_text = self._format_context(context_chunks)
                
                prompt = get_generation_prompt(
                    query=query,
                    mode="test_case",
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
                    return self.formatter.create_error_response(
                        query=query,
                        error_type="parse_error",
                        message="Failed to parse LLM response as JSON"
                    )
                
                if not self.formatter.validate_test_cases(parsed):
                    pass
                
                formatted = self.formatter.format_test_cases(parsed)
                
                test_stats = self._analyze_test_cases(formatted["test_cases"])
                formatted["test_statistics"] = test_stats
                
                formatted["tokens"] = response.get("tokens", {})
                formatted["model"] = response.get("model", "")
                formatted["success"] = True
                
                return formatted
        
        except Exception as e:
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
    
    def _analyze_test_cases(self, test_cases: List[Dict[str, Any]]) -> Dict[str, int]:
        stats = {
            "total": len(test_cases),
            "positive": 0,
            "negative": 0,
            "boundary": 0,
            "other": 0
        }
        
        for tc in test_cases:
            tc_type = tc.get("type", "").lower()
            if "positive" in tc_type:
                stats["positive"] += 1
            elif "negative" in tc_type:
                stats["negative"] += 1
            elif "boundary" in tc_type:
                stats["boundary"] += 1
            else:
                stats["other"] += 1
        
        return stats
