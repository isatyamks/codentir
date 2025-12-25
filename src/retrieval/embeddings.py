from typing import List, Dict, Any, Optional
from pathlib import Path

from src.config import settings
from src.utils import get_logger

logger = get_logger(__name__)


class EmbeddingModel:
    
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        self._initialize_sentence_transformers()
    
    def _initialize_sentence_transformers(self):
        try:
            from sentence_transformers import SentenceTransformer
            
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.embedding_type = "sentence-transformers"
            logger.info(f"Embedding model loaded successfully")
        
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    

    def embed_text(self, text: str) -> List[float]:
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return []
        
        try:
            embedding = self.model.encode(text, convert_to_tensor=False)
            embedding = embedding.tolist()
            
            return embedding
        
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return []
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        
        texts = [t for t in texts if t and t.strip()]
        
        if not texts:
            logger.warning("No valid texts to embed")
            return []
        
        try:
            embeddings = self.model.encode(
                texts,
                convert_to_tensor=False,
                batch_size=settings.BATCH_SIZE,
                show_progress_bar=len(texts) > 10
            )
            embeddings = embeddings.tolist()
            
            logger.info(f"Generated {len(embeddings)} embeddings")
            return embeddings
        
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            return []
    
    def get_embedding_dimension(self) -> int:
        try:
            return self.model.get_sentence_embedding_dimension()
        except Exception as e:
            logger.error(f"Error getting embedding dimension: {e}")
            return 384
    
    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "embedding_type": self.embedding_type,
            "dimension": self.get_embedding_dimension(),
            "max_seq_length": getattr(self.model, 'max_seq_length', None)
        }
