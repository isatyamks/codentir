from pathlib import Path
from typing import Optional
import io

from src.ingestion.parsers.base_parser import BaseParser, ParsedDocument
from src.utils import get_logger

logger = get_logger(__name__)


class PDFParser(BaseParser):
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = ['.pdf']
        self._check_dependencies()
    
    def _check_dependencies(self):
        try:
            import PyPDF2
            self.has_pypdf2 = True
        except ImportError:
            logger.warning("PyPDF2 not installed. PDF parsing may be limited.")
            self.has_pypdf2 = False
        
        try:
            import pdfplumber
            self.has_pdfplumber = True
        except ImportError:
            logger.warning("pdfplumber not installed. Using PyPDF2 only.")
            self.has_pdfplumber = False
        
        if not self.has_pypdf2 and not self.has_pdfplumber:
            raise ImportError(
                "Neither PyPDF2 nor pdfplumber is installed. "
                "Install with: pip install PyPDF2 pdfplumber"
            )
    
    def parse(self, file_path: Path) -> ParsedDocument:
        self.validate_file(file_path)
        logger.info(f"Parsing PDF file: {file_path.name}")
        
        if self.has_pdfplumber:
            content, metadata = self._parse_with_pdfplumber(file_path)
        else:
            content, metadata = self._parse_with_pypdf2(file_path)
        
        base_metadata = self.extract_basic_metadata(file_path)
        base_metadata.update(metadata)
        base_metadata["parser"] = "PDFParser"
        
        logger.info(
            f"Successfully parsed {file_path.name}: "
            f"{base_metadata.get('page_count', 0)} pages, "
            f"{len(content.split())} words"
        )
        
        return ParsedDocument(
            file_path=file_path,
            content=content,
            file_type="pdf",
            metadata=base_metadata
        )
    
    def _parse_with_pdfplumber(self, file_path: Path) -> tuple[str, dict]:
        import pdfplumber
        
        pages_text = []
        metadata = {}
        
        with pdfplumber.open(file_path) as pdf:
            metadata["page_count"] = len(pdf.pages)
            metadata["pdf_metadata"] = pdf.metadata or {}
            
            for i, page in enumerate(pdf.pages):
                try:
                    text = page.extract_text()
                    if text:
                        pages_text.append(f"[Page {i+1}]\n{text}")
                except Exception as e:
                    logger.warning(f"Error extracting page {i+1}: {e}")
                    pages_text.append(f"[Page {i+1}]\n[Error extracting text]")
        
        content = "\n\n".join(pages_text)
        metadata["extraction_method"] = "pdfplumber"
        
        return content, metadata
    
    def _parse_with_pypdf2(self, file_path: Path) -> tuple[str, dict]:
        import PyPDF2
        
        pages_text = []
        metadata = {}
        
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            metadata["page_count"] = len(pdf_reader.pages)
            
            if pdf_reader.metadata:
                metadata["pdf_metadata"] = {
                    k: str(v) for k, v in pdf_reader.metadata.items()
                }
            
            for i, page in enumerate(pdf_reader.pages):
                try:
                    text = page.extract_text()
                    if text:
                        pages_text.append(f"[Page {i+1}]\n{text}")
                except Exception as e:
                    logger.warning(f"Error extracting page {i+1}: {e}")
                    pages_text.append(f"[Page {i+1}]\n[Error extracting text]")
        
        content = "\n\n".join(pages_text)
        metadata["extraction_method"] = "PyPDF2"
        
        return content, metadata
