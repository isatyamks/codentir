from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

from src.ingestion.file_handler import FileHandler
from src.ingestion.chunker import TextChunker, TextChunk
from src.ingestion.parsers import ParsedDocument
from src.config import settings
from src.utils import get_logger, get_all_uploaded_files, timer, metrics_collector

logger = get_logger(__name__)


class IngestionPipeline:
    
    def __init__(self):
        self.file_handler = FileHandler()
        self.chunker = TextChunker()
        self.processed_dir = settings.base_dir / "data" / "processed"
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("IngestionPipeline initialized")
    
    def ingest_file(
        self,
        file_path: Path,
        chunk_strategy: str = "sliding_window"
    ) -> Dict[str, Any]:

        with timer(f"ingest_file_{file_path.name}"):
            logger.info(f"Starting ingestion for: {file_path.name}")
            
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
            
            logger.info(
                f"[OK] Ingested {file_path.name}: {len(chunks)} chunks created"
            )
            
            return result
    
    def ingest_directory(
        self,
        directory: Optional[Path] = None,
        chunk_strategy: str = "sliding_window"
    ) -> Dict[str, Any]:
        
        dir_path = directory or settings.upload_path
        
        logger.info(f"Starting batch ingestion from: {dir_path}")
        
        with timer(f"ingest_directory_{dir_path.name}"):
            files = get_all_uploaded_files() if directory is None else list(dir_path.rglob("*.*"))
            files = [f for f in files if f.is_file()]
            
            logger.info(f"Found {len(files)} files to process")
            
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
            
            logger.info(
                f"[OK] Batch ingestion complete: "
                f"{successful}/{len(files)} files, {total_chunks} chunks"
            )
            
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
            filename_base = parsed_doc.file_path.stem
            
            chunks_file = self.processed_dir / "chunks" / f"{filename_base}_chunks.json"
            chunks_file.parent.mkdir(parents=True, exist_ok=True)
            
            chunks_data = [chunk.to_dict() for chunk in chunks]
            
            with open(chunks_file, 'w', encoding='utf-8') as f:
                json.dump(chunks_data, f, indent=2, ensure_ascii=False)
            
            metadata_file = self.processed_dir / "metadata" / f"{filename_base}_metadata.json"
            metadata_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(parsed_doc.to_dict(), f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Saved processed data: {chunks_file.name}")
        
        except Exception as e:
            logger.error(f"Error saving processed data: {e}")
    
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
        from src.utils import clean_directory
        
        count = 0
        count += clean_directory(self.processed_dir / "chunks")
        count += clean_directory(self.processed_dir / "metadata")
        
        logger.info(f"Cleared {count} processed files")
        return count
