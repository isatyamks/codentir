from pathlib import Path
from typing import Optional

from src.ingestion.parsers.base_parser import BaseParser, ParsedDocument
from src.utils import get_logger

logger = get_logger(__name__)


class TextParser(BaseParser):
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = ['.txt', '.md', '.markdown', '.text']
    
    def parse(self, file_path: Path) -> ParsedDocument:
        self.validate_file(file_path)
        logger.info(f"Parsing text file: {file_path.name}")
        
        content = self._read_text_file(file_path)
        
        metadata = self.extract_basic_metadata(file_path)
        metadata.update({
            "parser": "TextParser",
            "encoding": self._detect_encoding(file_path),
            "line_count": content.count('\n') + 1,
            "word_count": len(content.split()),
            "char_count": len(content)
        })
        
        logger.info(
            f"Successfully parsed {file_path.name}: "
            f"{metadata['line_count']} lines, {metadata['word_count']} words"
        )
        
        return ParsedDocument(
            file_path=file_path,
            content=content,
            file_type="text",
            metadata=metadata
        )
    
    def _read_text_file(self, file_path: Path) -> str:
        encoding = self._detect_encoding(file_path)
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            return content
        except UnicodeDecodeError:
            logger.warning(f"Failed to read with {encoding}, trying utf-8")
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
    
    def _detect_encoding(self, file_path: Path) -> str:
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(4096)
            
            if raw_data.startswith(b'\xff\xfe') or raw_data.startswith(b'\xfe\xff'):
                return 'utf-16'
            elif raw_data.startswith(b'\xef\xbb\xbf'):
                return 'utf-8-sig'
            else:
                return 'utf-8'
        except Exception:
            return 'utf-8'
