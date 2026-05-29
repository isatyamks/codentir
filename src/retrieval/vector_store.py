from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import chromadb
from chromadb.config import Settings as ChromaSettings

from src.ingestion import TextChunk
from src.config import settings
from src.utils import timer

class VectorStore:
    def __init__(
        self,
        collection_name: Optional[str] = None,
        persist_directory: Optional[Path] = None
    ):
        self.collection_name = collection_name or settings.COLLECTION_NAME
        self.persist_directory = persist_directory or settings.vector_store_full_path
        self.client = None
        self.collection = None
        self._initialize_store()

    def _initialize_store(self):
        try:
            self.persist_directory.mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(path=str(self.persist_directory))
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Multimodal RAG knowledge base"}
            )
        except Exception as e:
            raise

    def add_chunks(self, chunks: List[TextChunk], embeddings: List[List[float]]) -> int:
        if not chunks or not embeddings:
            return 0
        if len(chunks) != len(embeddings):
            raise ValueError(f"Mismatch: {len(chunks)} chunks but {len(embeddings)} embeddings")

        try:
            with timer("add_chunks_to_vector_store"):
                ids = [chunk.chunk_id for chunk in chunks]
                documents = [chunk.content for chunk in chunks]
                
                metadatas = []
                for chunk in chunks:
                    metadata = chunk.metadata.copy() if chunk.metadata else {}
                    flat_metadata = {
                        k: str(v) if isinstance(v, (dict, list, tuple)) else v 
                        for k, v in metadata.items() if v is not None
                    }
                    if not flat_metadata:
                        flat_metadata = {"source": chunk.source_file, "chunk_index": chunk.chunk_index}
                    elif "source" not in flat_metadata:
                        flat_metadata["source"] = chunk.source_file
                    metadatas.append(flat_metadata)
                
                self.collection.upsert(
                    ids=ids,
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas
                )
                return len(chunks)
        except Exception as e:
            return 0

    def query(
        self,
        query_embedding: List[float],
        top_k: int = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        top_k = top_k or settings.TOP_K
        try:
            with timer("vector_store_query"):
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    where=filter_metadata
                )
                return {
                    'ids': results['ids'][0] if results['ids'] else [],
                    'documents': results['documents'][0] if results['documents'] else [],
                    'distances': results['distances'][0] if results['distances'] else [],
                    'metadatas': results['metadatas'][0] if results['metadatas'] else []
                }
        except Exception as e:
            return {'ids': [], 'documents': [], 'distances': [], 'metadatas': []}

    def similarity_search(
        self,
        query_text: str,
        query_embedding: List[float],
        top_k: int = None,
        threshold: float = None
    ) -> List[Dict[str, Any]]:
        threshold = threshold or settings.SIMILARITY_THRESHOLD
        top_k = top_k or settings.TOP_K
        
        results = self.query(query_embedding, top_k=top_k)
        formatted_results = []
        
        for i in range(len(results['ids'])):
            distance = results['distances'][i]
            similarity = 1 - distance
            if similarity >= threshold:
                formatted_results.append({
                    'chunk_id': results['ids'][i],
                    'content': results['documents'][i],
                    'similarity': round(similarity, 4),
                    'distance': round(distance, 4),
                    'metadata': results['metadatas'][i]
                })
        return formatted_results

    def delete_collection(self) -> bool:
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = None
            return True
        except Exception as e:
            return False

    def reset_collection(self) -> bool:
        try:
            self.delete_collection()
            self._initialize_store()
            return True
        except Exception as e:
            return False

    def get_stats(self) -> Dict[str, Any]:
        try:
            return {
                "collection_name": self.collection_name,
                "total_documents": self.collection.count(),
                "persist_directory": str(self.persist_directory),
            }
        except Exception as e:
            return {
                "collection_name": self.collection_name,
                "total_documents": 0,
                "error": str(e)
            }

    def get_by_ids(self, ids: List[str]) -> Dict[str, Any]:
        try:
            results = self.collection.get(ids=ids)
            return {
                'ids': results['ids'],
                'documents': results['documents'],
                'metadatas': results['metadatas']
            }
        except Exception as e:
            return {'ids': [], 'documents': [], 'metadatas': []}
