from typing import List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import re

from src.config import settings


@dataclass
class TextChunk:
    content: str
    chunk_id: str
    source_file: str
    chunk_index: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def word_count(self) -> int:
        return len(self.content.split())
    
    @property
    def char_count(self) -> int:
        return len(self.content)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "source_file": self.source_file,
            "chunk_index": self.chunk_index,
            "word_count": self.word_count,
            "char_count": self.char_count,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


class TextChunker:
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        min_chunk_size: int = None
    ):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        self.min_chunk_size = min_chunk_size or settings.MIN_CHUNK_SIZE
    
    def chunk_text(
        self,
        text: str,
        source_file: str,
        metadata: Dict[str, Any] = None
    ) -> List[TextChunk]:
        if not text or not text.strip():
            return []
        
        text = self._clean_text(text)
        
        chunks = self._create_chunks(text)
        
        chunk_objects = []
        for i, chunk_text in enumerate(chunks):
            if len(chunk_text.strip()) < self.min_chunk_size:
                continue
            
            chunk_id = f"{source_file}::chunk_{i}"
            
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata.update({
                "chunk_strategy": "sliding_window",
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap,
                "total_chunks": len(chunks)
            })
            
            chunk_obj = TextChunk(
                content=chunk_text.strip(),
                chunk_id=chunk_id,
                source_file=source_file,
                chunk_index=i,
                metadata=chunk_metadata
            )
            
            chunk_objects.append(chunk_obj)
        
        return chunk_objects
    
    def _create_chunks(self, text: str) -> List[str]:
        words = text.split()
        
        if len(words) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(words):
            end = start + self.chunk_size
            chunk_words = words[start:end]
            chunks.append(" ".join(chunk_words))
            
            if end >= len(words):
                break
            
            start += self.chunk_size - self.chunk_overlap
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        text = re.sub(r'\r\n', '\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        text = text.strip()
        
        return text
    
    def chunk_by_sentences(
        self,
        text: str,
        source_file: str,
        metadata: Dict[str, Any] = None
    ) -> List[TextChunk]:
        sentences = self._split_sentences(text)
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_words = len(sentence.split())
            
            if current_size + sentence_words > self.chunk_size and current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append(chunk_text)
                
                overlap_sentences = current_chunk[-2:] if len(current_chunk) > 1 else []
                current_chunk = overlap_sentences
                current_size = sum(len(s.split()) for s in current_chunk)
            
            current_chunk.append(sentence)
            current_size += sentence_words
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        chunk_objects = []
        for i, chunk_text in enumerate(chunks):
            if len(chunk_text.strip()) < self.min_chunk_size:
                continue
            
            chunk_id = f"{source_file}::chunk_{i}"
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata.update({
                "chunk_strategy": "sentence_based",
                "total_chunks": len(chunks)
            })
            
            chunk_obj = TextChunk(
                content=chunk_text.strip(),
                chunk_id=chunk_id,
                source_file=source_file,
                chunk_index=i,
                metadata=chunk_metadata
            )
            
            chunk_objects.append(chunk_obj)
        
        return chunk_objects
    
    def _split_sentences(self, text: str) -> List[str]:
        sentence_endings = r'[.!?]\s+'
        sentences = re.split(sentence_endings, text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    def chunk_by_paragraphs(
        self,
        text: str,
        source_file: str,
        metadata: Dict[str, Any] = None
    ) -> List[TextChunk]:
        paragraphs = text.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para_words = len(para.split())
            
            if current_size + para_words > self.chunk_size and current_chunk:
                chunk_text = "\n\n".join(current_chunk)
                chunks.append(chunk_text)
                current_chunk = []
                current_size = 0
            
            current_chunk.append(para)
            current_size += para_words
        
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))
        
        chunk_objects = []
        for i, chunk_text in enumerate(chunks):
            if len(chunk_text.strip()) < self.min_chunk_size:
                continue
            
            chunk_id = f"{source_file}::chunk_{i}"
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata.update({
                "chunk_strategy": "paragraph_based",
                "total_chunks": len(chunks)
            })
            
            chunk_obj = TextChunk(
                content=chunk_text.strip(),
                chunk_id=chunk_id,
                source_file=source_file,
                chunk_index=i,
                metadata=chunk_metadata
            )
            
            chunk_objects.append(chunk_obj)
        
        return chunk_objects
