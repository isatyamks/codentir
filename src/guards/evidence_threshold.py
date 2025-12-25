from typing import Dict, Any, List

from src.config import settings
from src.utils import get_logger

logger = get_logger(__name__)


class EvidenceThreshold:
    
    def __init__(
        self,
        min_confidence: float = None,
        min_chunks: int = 1
    ):
        self.min_confidence = min_confidence or settings.MIN_EVIDENCE_CONFIDENCE
        self.min_chunks = min_chunks
        
        logger.info(
            f"EvidenceThreshold initialized: "
            f"min_confidence={self.min_confidence}, min_chunks={self.min_chunks}"
        )
    
    def check_evidence(
        self,
        retrieval_results: List[Dict[str, Any]],
        query: str = ""
    ) -> Dict[str, Any]:
        
        if not retrieval_results:
            return {
                "sufficient": False,
                "reason": "no_results",
                "num_chunks": 0,
                "avg_confidence": 0.0,
                "recommendation": "ask_clarifying_questions"
            }
        
        num_chunks = len(retrieval_results)
        
        if num_chunks < self.min_chunks:
            return {
                "sufficient": False,
                "reason": "insufficient_chunks",
                "num_chunks": num_chunks,
                "min_required": self.min_chunks,
                "recommendation": "request_more_context"
            }
        
        scores = self._extract_scores(retrieval_results)
        
        if not scores:
            logger.warning("No scores found in retrieval results")
            return {
                "sufficient": False,
                "reason": "no_scores",
                "num_chunks": num_chunks,
                "recommendation": "retry_search"
            }
        
        avg_confidence = sum(scores) / len(scores)
        max_confidence = max(scores)
        min_confidence = min(scores)
        
        if avg_confidence < self.min_confidence:
            return {
                "sufficient": False,
                "reason": "low_confidence",
                "num_chunks": num_chunks,
                "avg_confidence": round(avg_confidence, 4),
                "max_confidence": round(max_confidence, 4),
                "min_confidence": round(min_confidence, 4),
                "threshold": self.min_confidence,
                "recommendation": "ask_clarifying_questions",
                "gap": round(self.min_confidence - avg_confidence, 4)
            }
        
        return {
            "sufficient": True,
            "num_chunks": num_chunks,
            "avg_confidence": round(avg_confidence, 4),
            "max_confidence": round(max_confidence, 4),
            "min_confidence": round(min_confidence, 4),
            "threshold": self.min_confidence,
            "recommendation": "proceed"
        }
    
    def _extract_scores(self, results: List[Dict[str, Any]]) -> List[float]:
        scores = []
        
        for result in results:
            if 'hybrid_score' in result:
                scores.append(result['hybrid_score'])
            elif 'similarity' in result:
                scores.append(result['similarity'])
            elif 'rerank_score' in result:
                scores.append(result['rerank_score'])
            elif 'bm25_score' in result:
                scores.append(result['bm25_score'])
        
        return scores
    
    def requires_clarification(
        self,
        retrieval_results: List[Dict[str, Any]]
    ) -> bool:
        
        check = self.check_evidence(retrieval_results)
        return not check["sufficient"]
    
    def get_clarification_prompt(
        self,
        query: str,
        check_result: Dict[str, Any]
    ) -> str:
        
        reason = check_result.get("reason", "unknown")
        
        if reason == "no_results":
            return (
                f"I couldn't find any relevant information about '{query}' "
                "in the available documents. Could you provide more context "
                "or rephrase your question?"
            )
        
        elif reason == "insufficient_chunks":
            return (
                f"I found only {check_result['num_chunks']} relevant passage(s) "
                f"about '{query}', which may not be enough for a complete answer. "
                "Could you provide more specific details or ask about a particular aspect?"
            )
        
        elif reason == "low_confidence":
            gap = check_result.get("gap", 0)
            return (
                f"The available information about '{query}' has low confidence "
                f"(score: {check_result['avg_confidence']:.2f}, "
                f"threshold: {check_result['threshold']:.2f}). "
                "Could you be more specific, or would you like me to make "
                "assumptions based on the limited information available?"
            )
        
        else:
            return (
                f"I don't have sufficient information to fully answer '{query}'. "
                "Could you provide more details?"
            )
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "min_confidence": self.min_confidence,
            "min_chunks": self.min_chunks,
            "enabled": settings.ENABLE_EVIDENCE_THRESHOLD
        }
