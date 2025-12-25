import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.utils import logger
from src.config import settings


def main():
    logger.info("=" * 60)
    logger.info("DevAssure - File-Based Multimodal RAG System")
    logger.info("=" * 60)
    logger.info(f"Version: 1.0.0")
    logger.info(f"Environment: {'DEBUG' if settings.DEBUG else 'PRODUCTION'}")
    logger.info(f"LLM Provider: {settings.get_llm_provider()}")
    logger.info(f"Upload Directory: {settings.upload_path}")
    logger.info(f"Vector Store: {settings.vector_store_full_path}")
    logger.info("=" * 60)
    
    try:
        import uvicorn
        from main import app
        
        logger.info(f"Starting API server on {settings.API_HOST}:{settings.API_PORT}")
        
        uvicorn.run(
            app,
            host=settings.API_HOST,
            port=settings.API_PORT,
            reload=settings.API_RELOAD,
            log_level=settings.LOG_LEVEL.lower()
        )
    
    except ImportError as e:
        logger.error(f"Failed to import required modules: {e}")
        logger.error("Please ensure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("Shutting down DevAssure...")
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
