from typing import List, Dict, Any, Optional

from src.config import settings

class Reranker:
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-12-v2"):
        self.model_name = model_name
        self.model = None
        
        if settings.ENABLE_RERANKING:
            self._initialize_model()
    def _initialize_model(self):
        try:
            from sentence_transformers import CrossEncoder
            
            self.model = CrossEncoder(self.model_name)
        
        except ImportError:
            self.model = None
        
        except Exception as e:
            self.model = None
    
    def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        if not self.model:
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
            
            return reranked_results
        
        except Exception as e:
            return results
    
    def is_available(self) -> bool:
        return self.model is not None
