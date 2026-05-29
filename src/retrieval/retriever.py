from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json

from src.retrieval.embeddings import EmbeddingModel
from src.retrieval.vector_store import VectorStore
from src.retrieval.hybrid_search import HybridSearch
from src.retrieval.reranker import Reranker
from src.ingestion import TextChunk, IngestionPipeline
from src.config import settings
from src.utils import timer, metrics_collector

class Retriever:
    def __init__(self):
        self.embedding_model = EmbeddingModel()
        self.vector_store = VectorStore()
        self.hybrid_search = HybridSearch(
            vector_store=self.vector_store,
            embedding_model=self.embedding_model
        )
        self.reranker = Reranker() if settings.ENABLE_RERANKING else None
        self.ingestion_pipeline = IngestionPipeline()

    def _load_persisted_chunks(self, file_paths: Optional[List[Path]] = None) -> Tuple[List[str], List[TextChunk]]:
        processed_dir = settings.base_dir / "data" / "processed" / "chunks"
        if not processed_dir.exists():
            return [], []

        chunk_files = []
        if file_paths:
            for file_path in file_paths:
                json_path = processed_dir / f"{file_path.stem}_chunks.json"
                if json_path.exists():
                    chunk_files.append(json_path)
        else:
            chunk_files = list(processed_dir.glob("*.json"))

        all_contents = []
        all_chunks_obj = []
        seen_ids = set()

        for chunk_file in chunk_files:
            with open(chunk_file, 'r', encoding='utf-8') as f:
                chunks_data = json.load(f)
                for chunk_data in chunks_data:
                    chunk_id = chunk_data['chunk_id']
                    if chunk_id in seen_ids:
                        continue
                    seen_ids.add(chunk_id)
                    all_contents.append(chunk_data['content'])
                    all_chunks_obj.append(TextChunk(
                        content=chunk_data['content'],
                        chunk_id=chunk_id,
                        source_file=chunk_data['source_file'],
                        chunk_index=chunk_data['chunk_index'],
                        metadata=chunk_data.get('metadata', {})
                    ))
        return all_contents, all_chunks_obj

    def index_documents(
        self,
        file_paths: Optional[List[Path]] = None,
        directory: Optional[Path] = None,
        chunk_strategy: str = "sliding_window"
    ) -> Dict[str, Any]:
        with timer("index_documents"):
            if directory:
                self.ingestion_pipeline.ingest_directory(directory=directory, chunk_strategy=chunk_strategy)
            elif file_paths:
                for file_path in file_paths:
                    self.ingestion_pipeline.ingest_file(file_path=file_path, chunk_strategy=chunk_strategy)
            else:
                return self.index_documents(directory=settings.upload_path, chunk_strategy=chunk_strategy)

            all_contents, all_chunks_obj = self._load_persisted_chunks(file_paths)
            
            if not all_contents:
                return {"success": False, "error": "No content found in chunks"}

            embeddings = self.embedding_model.embed_batch(all_contents)
            if not embeddings:
                return {"success": False, "error": "Failed to generate embeddings"}

            added_count = self.vector_store.add_chunks(all_chunks_obj, embeddings)
            self.hybrid_search.build_bm25_index()
            metrics_collector.increment_counter("documents_indexed", added_count)

            return {
                "success": True,
                "chunks_indexed": added_count,
                "embedding_dimension": self.embedding_model.get_embedding_dimension(),
                "vector_store_stats": self.vector_store.get_stats()
            }

    def retrieve(
        self,
        query: str,
        top_k: int = None,
        search_mode: str = "hybrid",
        use_reranking: bool = None
    ) -> List[Dict[str, Any]]:
        top_k = top_k or settings.TOP_K
        use_reranking = use_reranking if use_reranking is not None else settings.ENABLE_RERANKING
        
        with timer("retrieve"):
            candidate_k = settings.RERANK_TOP_K if use_reranking else top_k
            results = self.hybrid_search.get_search_mode_results(query=query, mode=search_mode, top_k=candidate_k)
            
            if not results:
                return []
            
            if use_reranking and self.reranker and self.reranker.is_available():
                results = self.reranker.rerank(query, results, top_k=top_k)
            else:
                results = results[:top_k]
            
            metrics_collector.increment_counter("queries_processed")
            return results

    def retrieve_with_context(
        self,
        query: str,
        top_k: int = None,
        search_mode: str = "hybrid"
    ) -> Dict[str, Any]:
        results = self.retrieve(query, top_k, search_mode)
        if not results:
            return {
                "query": query, "context_found": False, "num_chunks": 0,
                "avg_score": 0.0, "chunks": [], "context_text": ""
            }
        
        scores = []
        if 'hybrid_score' in results[0]: scores = [r['hybrid_score'] for r in results]
        elif 'similarity' in results[0]: scores = [r['similarity'] for r in results]
        elif 'bm25_score' in results[0]: scores = [r['bm25_score'] for r in results]
        
        avg_score = sum(scores) / len(scores) if scores else 0.0
        
        context_chunks = []
        for i, result in enumerate(results):
            score_val = scores[i] if i < len(scores) else 0.0
            source_val = result.get('metadata', {}).get('file_name', 'unknown')
            context_chunks.append(f"[Chunk {i+1}] (Score: {score_val:.3f})\nSource: {source_val}\n{result['content']}\n")
        
        return {
            "query": query,
            "context_found": True,
            "num_chunks": len(results),
            "avg_score": round(avg_score, 4),
            "chunks": results,
            "context_text": "\n---\n".join(context_chunks),
            "search_mode": search_mode
        }

    def get_retriever_stats(self) -> Dict[str, Any]:
        return {
            "vector_store": self.vector_store.get_stats(),
            "embedding_model": self.embedding_model.get_model_info(),
            "reranking_enabled": self.reranker is not None and self.reranker.is_available(),
            "search_config": {
                "top_k": settings.TOP_K,
                "similarity_threshold": settings.SIMILARITY_THRESHOLD,
                "hybrid_alpha": settings.HYBRID_ALPHA,
                "rerank_top_k": settings.RERANK_TOP_K
            },
            "metrics": {
                "documents_indexed": metrics_collector.get_counter("documents_indexed"),
                "queries_processed": metrics_collector.get_counter("queries_processed")
            }
        }

    def reset_index(self) -> bool:
        success = self.vector_store.reset_collection()
        if success:
            self.hybrid_search.bm25_index = None
        return success
