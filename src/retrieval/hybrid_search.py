from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
import numpy as np

from src.config import settings
from src.utils import timer


class HybridSearch:
    
    def __init__(
        self,
        vector_store,
        embedding_model,
        alpha: float = None
    ):
        self.vector_store = vector_store
        self.embedding_model = embedding_model
        self.alpha = alpha if alpha is not None else settings.HYBRID_ALPHA
        
        self.bm25_index = None
        self.document_ids = []
        self.documents = []
    
    def build_bm25_index(self) -> bool:
        try:
            with timer("build_bm25_index"):
                stats = self.vector_store.get_stats()
                total_docs = stats.get('total_documents', 0)
                
                if total_docs == 0:
                    return False
                
                all_docs = self.vector_store.collection.get()
                
                self.document_ids = all_docs['ids']
                self.documents = all_docs['documents']
                
                tokenized_docs = [doc.lower().split() for doc in self.documents]
                
                self.bm25_index = BM25Okapi(tokenized_docs)
                
                return True
        
        except Exception as e:
            return False
    
    def bm25_search(
        self,
        query: str,
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        if self.bm25_index is None:
            self.build_bm25_index()
        
        if self.bm25_index is None:
            return []
        
        top_k = top_k or settings.TOP_K
        
        try:
            with timer("bm25_search"):
                tokenized_query = query.lower().split()
                
                scores = self.bm25_index.get_scores(tokenized_query)
                
                top_indices = np.argsort(scores)[::-1][:top_k]
                
                results = []
                for idx in top_indices:
                    if scores[idx] > 0:
                        results.append({
                            'chunk_id': self.document_ids[idx],
                            'content': self.documents[idx],
                            'bm25_score': float(scores[idx]),
                            'rank': len(results) + 1
                        })
                
                return results
        
        except Exception as e:
            return []
    
    def vector_search(
        self,
        query: str,
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        top_k = top_k or settings.TOP_K
        
        try:
            with timer("vector_search"):
                query_embedding = self.embedding_model.embed_text(query)
                
                if not query_embedding:
                    return []
                
                results = self.vector_store.similarity_search(
                    query_text=query,
                    query_embedding=query_embedding,
                    top_k=top_k,
                    threshold=0.0
                )
                
                return results
        
        except Exception as e:
            return []
    
    def hybrid_search(
        self,
        query: str,
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        top_k = top_k or settings.TOP_K
        
        try:
            with timer("hybrid_search"):
                vector_results = self.vector_search(query, top_k=top_k * 2)
                bm25_results = self.bm25_search(query, top_k=top_k * 2)
                
                combined_scores = {}
                
                max_bm25 = max([r['bm25_score'] for r in bm25_results]) if bm25_results else 1.0
                max_vector = max([r['similarity'] for r in vector_results]) if vector_results else 1.0
                
                for result in vector_results:
                    chunk_id = result['chunk_id']
                    normalized_vector_score = result['similarity'] / max_vector if max_vector > 0 else 0
                    combined_scores[chunk_id] = {
                        'vector_score': normalized_vector_score,
                        'bm25_score': 0.0,
                        'content': result['content'],
                        'metadata': result.get('metadata', {})
                    }
                
                for result in bm25_results:
                    chunk_id = result['chunk_id']
                    normalized_bm25_score = result['bm25_score'] / max_bm25 if max_bm25 > 0 else 0
                    
                    if chunk_id in combined_scores:
                        combined_scores[chunk_id]['bm25_score'] = normalized_bm25_score
                    else:
                        combined_scores[chunk_id] = {
                            'vector_score': 0.0,
                            'bm25_score': normalized_bm25_score,
                            'content': result['content'],
                            'metadata': {}
                        }
                
                for chunk_id, scores in combined_scores.items():
                    hybrid_score = (
                        self.alpha * scores['vector_score'] +
                        (1 - self.alpha) * scores['bm25_score']
                    )
                    scores['hybrid_score'] = hybrid_score
                
                sorted_results = sorted(
                    combined_scores.items(),
                    key=lambda x: x[1]['hybrid_score'],
                    reverse=True
                )[:top_k]
                
                formatted_results = []
                for chunk_id, scores in sorted_results:
                    formatted_results.append({
                        'chunk_id': chunk_id,
                        'content': scores['content'],
                        'hybrid_score': round(scores['hybrid_score'], 4),
                        'vector_score': round(scores['vector_score'], 4),
                        'bm25_score': round(scores['bm25_score'], 4),
                        'metadata': scores['metadata']
                    })
                
                return formatted_results
        
        except Exception as e:
            return []
    
    def get_search_mode_results(
        self,
        query: str,
        mode: str = "hybrid",
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        if mode == "vector":
            return self.vector_search(query, top_k)
        elif mode == "keyword" or mode == "bm25":
            return self.bm25_search(query, top_k)
        else:
            return self.hybrid_search(query, top_k)
