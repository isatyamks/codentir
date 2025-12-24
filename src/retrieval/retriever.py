from typing import List, Dict, Any, Optional
from pathlib import Path

from src.retrieval.embeddings import EmbeddingModel
from src.retrieval.vector_store import VectorStore
from src.retrieval.hybrid_search import HybridSearch
from src.retrieval.reranker import Reranker
from src.ingestion import TextChunk, IngestionPipeline
from src.config import settings
from src.utils import get_logger, timer, metrics_collector

logger = get_logger(__name__)


class Retriever:
    
    def __init__(self):
        logger.info("Initializing Retriever...")
        
        self.embedding_model = EmbeddingModel()
        self.vector_store = VectorStore()
        self.hybrid_search = HybridSearch(
            vector_store=self.vector_store,
            embedding_model=self.embedding_model
        )
        self.reranker = Reranker() if settings.ENABLE_RERANKING else None
        
        self.ingestion_pipeline = IngestionPipeline()
        
        logger.info("Retriever initialized successfully")
    
    def index_documents(
        self,
        file_paths: Optional[List[Path]] = None,
        directory: Optional[Path] = None,
        chunk_strategy: str = "sliding_window"
    ) -> Dict[str, Any]:
    
        logger.info("Starting document indexing...")
        
        with timer("index_documents"):
            if directory:
                ingestion_result = self.ingestion_pipeline.ingest_directory(
                    directory=directory,
                    chunk_strategy=chunk_strategy
                )
                chunks_data = []
                for result in ingestion_result['results']:
                    if result['success']:
                        pass
            
            elif file_paths:
                all_chunks = []
                for file_path in file_paths:
                    result = self.ingestion_pipeline.ingest_file(
                        file_path=file_path,
                        chunk_strategy=chunk_strategy
                    )
                    if result['success']:
                        pass
            
            else:
                directory = settings.upload_path
                return self.index_documents(directory=directory, chunk_strategy=chunk_strategy)
            
            from pathlib import Path
            import json
            
            processed_dir = settings.base_dir / "data" / "processed" / "chunks"
            
            if not processed_dir.exists():
                logger.warning("No processed chunks found")
                return {
                    "success": False,
                    "error": "No processed chunks to index"
                }
            
            chunk_files = list(processed_dir.glob("*.json"))
            
            if not chunk_files:
                logger.warning("No chunk files found")
                return {
                    "success": False,
                    "error": "No chunk files found"
                }
            
            all_contents = []
            all_chunks_obj = []
            seen_ids = set()
            
            for chunk_file in chunk_files:
                with open(chunk_file, 'r', encoding='utf-8') as f:
                    chunks_data = json.load(f)
                    for chunk_data in chunks_data:
                        chunk_id = chunk_data['chunk_id']
                        
                        if chunk_id in seen_ids:
                            logger.debug(f"Skipping duplicate chunk: {chunk_id}")
                            continue
                        
                        seen_ids.add(chunk_id)
                        all_contents.append(chunk_data['content'])
                        
                        chunk_obj = TextChunk(
                            content=chunk_data['content'],
                            chunk_id=chunk_id,
                            source_file=chunk_data['source_file'],
                            chunk_index=chunk_data['chunk_index'],
                            metadata=chunk_data.get('metadata', {})
                        )
                        all_chunks_obj.append(chunk_obj)
            
            if not all_contents:
                logger.warning("No content to embed")
                return {
                    "success": False,
                    "error": "No content found in chunks"
                }
            
            logger.info(f"Generating embeddings for {len(all_contents)} chunks...")
            embeddings = self.embedding_model.embed_batch(all_contents)
            
            if not embeddings:
                logger.error("Failed to generate embeddings")
                return {
                    "success": False,
                    "error": "Failed to generate embeddings"
                }
            
            logger.info("Adding chunks to vector store...")
            added_count = self.vector_store.add_chunks(all_chunks_obj, embeddings)
            
            logger.info("Building BM25 index...")
            self.hybrid_search.build_bm25_index()
            
            metrics_collector.increment_counter("documents_indexed", added_count)
            
            result = {
                "success": True,
                "chunks_indexed": added_count,
                "embedding_dimension": self.embedding_model.get_embedding_dimension(),
                "vector_store_stats": self.vector_store.get_stats()
            }
            
            logger.info(f"Indexing complete: {added_count} chunks indexed")
            return result
    
    def retrieve(
        self,
        query: str,
        top_k: int = None,
        search_mode: str = "hybrid",
        use_reranking: bool = None
    ) -> List[Dict[str, Any]]:
       
        top_k = top_k or settings.TOP_K
        use_reranking = use_reranking if use_reranking is not None else settings.ENABLE_RERANKING
        
        logger.info(f"Retrieving documents for query: '{query[:50]}...'")
        
        with timer("retrieve"):
            candidate_k = settings.RERANK_TOP_K if use_reranking else top_k
            
            results = self.hybrid_search.get_search_mode_results(
                query=query,
                mode=search_mode,
                top_k=candidate_k
            )
            
            if not results:
                logger.warning("No results found")
                return []
            
            if use_reranking and self.reranker and self.reranker.is_available():
                logger.info("Reranking results...")
                results = self.reranker.rerank(query, results, top_k=top_k)
            else:
                results = results[:top_k]
            
            metrics_collector.increment_counter("queries_processed")
            
            logger.info(f"Retrieved {len(results)} documents")
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
                "query": query,
                "context_found": False,
                "num_chunks": 0,
                "avg_score": 0.0,
                "chunks": [],
                "context_text": ""
            }
        
        scores = []
        if 'hybrid_score' in results[0]:
            scores = [r['hybrid_score'] for r in results]
        elif 'similarity' in results[0]:
            scores = [r['similarity'] for r in results]
        elif 'bm25_score' in results[0]:
            scores = [r['bm25_score'] for r in results]
        
        avg_score = sum(scores) / len(scores) if scores else 0.0
        
        context_chunks = []
        for i, result in enumerate(results):
            context_chunks.append(
                f"[Chunk {i+1}] (Score: {scores[i] if i < len(scores) else 0.0:.3f})\n"
                f"Source: {result.get('metadata', {}).get('file_name', 'unknown')}\n"
                f"{result['content']}\n"
            )
        
        context_text = "\n---\n".join(context_chunks)
        
        return {
            "query": query,
            "context_found": True,
            "num_chunks": len(results),
            "avg_score": round(avg_score, 4),
            "chunks": results,
            "context_text": context_text,
            "search_mode": search_mode
        }
    
    def get_retriever_stats(self) -> Dict[str, Any]:
        """Get statistics about the retriever"""
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
        """Reset the vector store index"""
        logger.warning("Resetting vector store index...")
        success = self.vector_store.reset_collection()
        if success:
            self.hybrid_search.bm25_index = None
        return success
