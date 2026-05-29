from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

from src.ingestion.file_handler import FileHandler
from src.ingestion.chunker import TextChunker, TextChunk
from src.ingestion.parsers import ParsedDocument
from src.config import settings
from src.utils import get_all_uploaded_files, timer, metrics_collector


class IngestionPipeline:
    
    def __init__(self):
        self.file_handler = FileHandler()
        self.chunker = TextChunker()
        
    def ingest_file(
        self,
        file_path: Path,
        chunk_strategy: str = "sliding_window"
    ) -> Dict[str, Any]:

        with timer(f"ingest_file_{file_path.name}"):
            
            parsed_doc = self.file_handler.parse_file(file_path)
            if not parsed_doc:
                return {
                    "success": False,
                    "file": str(file_path),
                    "error": "Failed to parse file"
                }
            
            chunks = self._chunk_document(parsed_doc, chunk_strategy)
            
            self._save_processed_data(parsed_doc, chunks)
            
            metrics_collector.increment_counter("files_ingested")
            metrics_collector.increment_counter("chunks_created", len(chunks))
            
            result = {
                "success": True,
                "file": str(file_path),
                "file_type": parsed_doc.file_type,
                "content_length": len(parsed_doc.content),
                "chunks_created": len(chunks),
                "chunk_strategy": chunk_strategy,
                "metadata": parsed_doc.metadata
            }
            
            return result
    
    def ingest_directory(
        self,
        directory: Optional[Path] = None,
        chunk_strategy: str = "sliding_window"
    ) -> Dict[str, Any]:
        
        dir_path = directory or settings.upload_path
        
        with timer(f"ingest_directory_{dir_path.name}"):
            files = get_all_uploaded_files() if directory is None else list(dir_path.rglob("*.*"))
            files = [f for f in files if f.is_file()]
            
            results = []
            successful = 0
            failed = 0
            total_chunks = 0
            
            for file_path in files:
                result = self.ingest_file(file_path, chunk_strategy)
                results.append(result)
                
                if result["success"]:
                    successful += 1
                    total_chunks += result["chunks_created"]
                else:
                    failed += 1
            
            summary = {
                "success": True,
                "directory": str(dir_path),
                "total_files": len(files),
                "successful": successful,
                "failed": failed,
                "total_chunks": total_chunks,
                "chunk_strategy": chunk_strategy,
                "results": results
            }
            
            return summary
    
    def _chunk_document(
        self,
        parsed_doc: ParsedDocument,
        strategy: str
    ) -> List[TextChunk]:
        if strategy == "sentence_based":
            chunks = self.chunker.chunk_by_sentences(
                parsed_doc.content,
                str(parsed_doc.file_path),
                parsed_doc.metadata
            )
        elif strategy == "paragraph_based":
            chunks = self.chunker.chunk_by_paragraphs(
                parsed_doc.content,
                str(parsed_doc.file_path),
                parsed_doc.metadata
            )
        else:
            chunks = self.chunker.chunk_text(
                parsed_doc.content,
                str(parsed_doc.file_path),
                parsed_doc.metadata
            )
        
        return chunks
    
    def _save_processed_data(
        self,
        parsed_doc: ParsedDocument,
        chunks: List[TextChunk]
    ) -> None:
        try:
            from src.utils.db_manager import DBManager
            db = DBManager()
            
            doc_metadata = parsed_doc.to_dict()
            chunks_data = [chunk.to_dict() for chunk in chunks]
            
            db.save_processed_document(doc_metadata, chunks_data)
        
        except Exception as e:
            pass
    
    def get_ingestion_stats(self) -> Dict[str, Any]:
        return {
            "files_ingested": metrics_collector.get_counter("files_ingested"),
            "chunks_created": metrics_collector.get_counter("chunks_created"),
            "supported_extensions": self.file_handler.get_supported_extensions(),
            "parser_info": self.file_handler.get_parser_info(),
            "chunk_config": {
                "chunk_size": self.chunker.chunk_size,
                "chunk_overlap": self.chunker.chunk_overlap,
                "min_chunk_size": self.chunker.min_chunk_size
            }
        }
    
    def clear_processed_data(self) -> int:
        from src.utils.db_manager import DBManager
        db = DBManager()
        
        count = 0
        if db.db is not None:
            doc_result = db.documents.delete_many({})
            chunk_result = db.chunks.delete_many({})
            count = doc_result.deleted_count + chunk_result.deleted_count
            
        return count
