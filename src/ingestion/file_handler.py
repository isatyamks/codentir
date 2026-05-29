from pathlib import Path
from typing import List, Optional, Dict, Any

from src.ingestion.parsers import (
    BaseParser,
    ParsedDocument,
    TextParser,
    PDFParser,
    DOCXParser,
    ImageParser
)
from src.utils import get_file_type, validate_file


class FileHandler:
    
    def __init__(self):
        self.parsers: List[BaseParser] = []
        self._initialize_parsers()
    
    def _initialize_parsers(self):
        try:
            self.parsers.append(TextParser())
        except Exception as e:
            pass
        
        try:
            self.parsers.append(PDFParser())
        except Exception as e:
            pass
        
        try:
            self.parsers.append(DOCXParser())
        except Exception as e:
            pass
        
        try:
            self.parsers.append(ImageParser())
        except Exception as e:
            pass
    
    def get_parser(self, file_path: Path) -> Optional[BaseParser]:
        
        for parser in self.parsers:
            if parser.can_parse(file_path):
                return parser
        
        return None
    
    def parse_file(self, file_path: Path) -> Optional[ParsedDocument]:
        
        is_valid, error = validate_file(file_path)
        if not is_valid:
            return None
        
        parser = self.get_parser(file_path)
        if not parser:
            return None
        
        try:
            parsed_doc = parser.parse(file_path)
            return parsed_doc
        
        except Exception as e:
            return None
    
    def parse_multiple_files(self, file_paths: List[Path]) -> List[ParsedDocument]:
        
        parsed_docs = []
        
        for file_path in file_paths:
            parsed_doc = self.parse_file(file_path)
            if parsed_doc:
                parsed_docs.append(parsed_doc)
        
        return parsed_docs
    
    def get_supported_extensions(self) -> List[str]:
        extensions = set()
        for parser in self.parsers:
            extensions.update(parser.supported_extensions)
        return sorted(list(extensions))
    
    def get_parser_info(self) -> Dict[str, Any]:
        info = {
            "total_parsers": len(self.parsers),
            "parsers": []
        }
        
        for parser in self.parsers:
            info["parsers"].append({
                "name": parser.__class__.__name__,
                "supported_extensions": parser.supported_extensions
            })
        
        info["all_supported_extensions"] = self.get_supported_extensions()
        
        return info
