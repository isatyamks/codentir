from pathlib import Path
from typing import Optional
import tempfile

from src.ingestion.parsers.base_parser import BaseParser, ParsedDocument
from src.config import settings
from src.utils import get_logger

logger = get_logger(__name__)


class ImageParser(BaseParser):
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff']
        self.ocr_engine = self._initialize_ocr()
    
    def _initialize_ocr(self) -> str:
        if settings.USE_EASYOCR:
            try:
                import easyocr
                self.reader = easyocr.Reader([settings.OCR_LANGUAGE])
                logger.info("Initialized EasyOCR")
                return "easyocr"
            except ImportError:
                logger.warning("EasyOCR not available, falling back to Tesseract")
        
        try:
            import pytesseract
            from PIL import Image
            
            if settings.TESSERACT_PATH and Path(settings.TESSERACT_PATH).exists():
                pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_PATH
            
            logger.info("Initialized Tesseract OCR")
            return "tesseract"
        
        except ImportError:
            logger.warning(
                "No OCR engine available. Install with: "
                "pip install pytesseract pillow OR pip install easyocr"
            )
            return "none"
    
    def parse(self, file_path: Path) -> ParsedDocument:
        self.validate_file(file_path)
        logger.info(f"Parsing image file: {file_path.name}")
        
        if self.ocr_engine == "none":
            raise RuntimeError(
                "No OCR engine available. "
                "Install pytesseract/pillow or easyocr"
            )
        
        if self.ocr_engine == "easyocr":
            content = self._extract_with_easyocr(file_path)
        else:
            content = self._extract_with_tesseract(file_path)
        
        metadata = self.extract_basic_metadata(file_path)
        metadata.update(self._extract_image_metadata(file_path))
        metadata.update({
            "parser": "ImageParser",
            "ocr_engine": self.ocr_engine,
            "extracted_text_length": len(content),
            "word_count": len(content.split())
        })
        
        logger.info(
            f"Successfully parsed {file_path.name} using {self.ocr_engine}: "
            f"{metadata['word_count']} words extracted"
        )
        
        return ParsedDocument(
            file_path=file_path,
            content=content,
            file_type="image",
            metadata=metadata
        )
    
    def _extract_with_tesseract(self, file_path: Path) -> str:
        import pytesseract
        from PIL import Image
        
        try:
            image = Image.open(file_path)
            
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            text = pytesseract.image_to_string(
                image,
                lang=settings.OCR_LANGUAGE
            )
            
            return text.strip()
        except Exception as e:
            logger.error(f"Tesseract OCR failed: {e}")
            return ""
    
    def _extract_with_easyocr(self, file_path: Path) -> str:
        try:
            result = self.reader.readtext(str(file_path))
            texts = [text for (bbox, text, conf) in result if conf > 0.3]
            return "\n".join(texts)
        except Exception as e:
            logger.error(f"EasyOCR failed: {e}")
            return ""
    
    def _extract_image_metadata(self, file_path: Path) -> dict:
        try:
            from PIL import Image
            
            with Image.open(file_path) as img:
                return {
                    "image_width": img.width,
                    "image_height": img.height,
                    "image_format": img.format,
                    "image_mode": img.mode,
                }
        except Exception as e:
            logger.warning(f"Could not extract image metadata: {e}")
            return {}
