from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict



class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="allow"
    )

    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    VECTOR_STORE_PATH: str = "./data/vector_store"
    COLLECTION_NAME: str = "rag_knowledge"

    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    MIN_CHUNK_SIZE: int = 100

    # OCR Settings
    USE_EASYOCR: bool = False
    OCR_LANGUAGE: str = "eng"
    TESSERACT_PATH: Optional[str] = None

    TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.7
    HYBRID_ALPHA: float = 0.5
    ENABLE_RERANKING: bool = False
    RERANK_TOP_K: int = 10

    MIN_EVIDENCE_CONFIDENCE: float = 0.3
    MAX_CONTEXT_DEVIATION: float = 0.3
    ENABLE_HALLUCINATION_GUARD: bool = True
    ENABLE_PROMPT_INJECTION_GUARD: bool = True
    ENABLE_EVIDENCE_THRESHOLD: bool = False

    LLM_TEMPERATURE: float = 0.2
    MAX_TOKENS: int = 2000
    REQUIRE_JSON_MODE: bool = True

    UPLOAD_DIR: str = "./data/uploads"
    MONGO_URI: str = "mongodb://localhost:27017/"
    MONGO_DB_NAME: str = "multimodal_rag"
    MAX_FILE_SIZE: int = 10485760
    ALLOWED_EXTENSIONS: str = ".txt,.md,.pdf,.docx,.png,.jpg,.jpeg"

    LOG_LEVEL: str = "info"

    BATCH_SIZE: int = 32
    MAX_WORKERS: int = 4
    ENABLE_CACHE: bool = True
    CACHE_DIR: str = "./data/cache"

    LOG_DIR: str = "./logs"
    LOG_FILE: str = "app.log"
    LOG_MAX_BYTES: int = 10485760
    LOG_BACKUP_COUNT: int = 5

    DEBUG: bool = False
    ENABLE_PROFILING: bool = False

    @property
    def base_dir(self) -> Path:
        return Path(__file__).parent.parent.parent

    @property
    def upload_path(self) -> Path:
        return self.base_dir / self.UPLOAD_DIR.lstrip("./")

    @property
    def vector_store_full_path(self) -> Path:
        return self.base_dir / self.VECTOR_STORE_PATH.lstrip("./")

    @property
    def log_path(self) -> Path:
        return self.base_dir / self.LOG_DIR.lstrip("./")

    @property
    def cache_path(self) -> Path:
        return self.base_dir / self.CACHE_DIR.lstrip("./")

    @property
    def allowed_extensions_list(self) -> list[str]:
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")]

    def get_llm_provider(self) -> str:
        if self.GROQ_API_KEY:
            return "groq"
        else:
            raise ValueError("GROQ_API_KEY is required. Only Groq is supported.")

    def ensure_directories(self) -> None:
        self.upload_path.mkdir(parents=True, exist_ok=True)
        self.vector_store_full_path.mkdir(parents=True, exist_ok=True)
        self.log_path.mkdir(parents=True, exist_ok=True)
        if self.ENABLE_CACHE:
            self.cache_path.mkdir(parents=True, exist_ok=True)


settings = Settings()
