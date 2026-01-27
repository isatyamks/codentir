from typing import List, Dict, Any, Optional

from src.config import settings
from src.utils import get_logger

logger = get_logger(__name__)


class Reranker:
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-12-v2"):
        self.model_name = model_name
        self.model = None
        
        if settings.ENABLE_RERANKING:
            self._initialize_model()
    def _initialize_model(self):
        try:
            from sentence_transformers import CrossEncoder
            
            logger.info(f"Loading reranker model: {self.model_name}")
            self.model = CrossEncoder(self.model_name)
            logger.info("Reranker model loaded successfully")
        
        except ImportError:
            logger.warning(
                "sentence-transformers not available. "
                "Reranking disabled. Install with: pip install sentence-transformers"
            )
            self.model = None
        
        except Exception as e:
            logger.error(f"Failed to load reranker model: {e}")
            self.model = None
    
    def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        if not self.model:
            logger.warning("Reranker not available, returning original results")
            return results
        
        if not results:
            return results
        
        top_k = top_k or settings.RERANK_TOP_K or len(results)
        
        try:
            query_doc_pairs = [
                [query, result['content']]
                for result in results
            ]
            
            scores = self.model.predict(query_doc_pairs)
            
            for i, result in enumerate(results):
                result['rerank_score'] = float(scores[i])
                result['original_rank'] = i+1
            
            reranked_results = sorted(
                results,
                key=lambda x: x['rerank_score'],
                reverse=True
            )[:top_k]
            
            for i, result in enumerate(reranked_results):
                result['new_rank'] = i + 1
            
            logger.info(
                f"Reranked {len(results)} results, returning top {len(reranked_results)}"
            )
            
            return reranked_results
        
        except Exception as e:
            logger.error(f"Error during reranking: {e}")
            return results
    
    def is_available(self) -> bool:
        return self.model is not None
