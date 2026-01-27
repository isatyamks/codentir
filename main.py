from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List
from pathlib import Path
import shutil

from src.config import settings
from src.generation import Generator
from src.retrieval import Retriever
from src.utils import get_logger

logger = get_logger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

generator = None
retriever = None


@app.on_event("startup")
async def startup_event():
    global generator, retriever
    
    logger.info("Starting DevAssure RAG API...")
    
    try:
        generator = Generator()
        retriever = Retriever()
        
        logger.info("API initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize API: {e}")
        raise


@app.get("/")
async def root():
    return {
        "name": "DevAssure RAG API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "upload": "/upload",
            "generate_use_case": "/generate/use-case",
            "generate_test_cases": "/generate/test-cases",
            "query": "/query",
            "stats": "/stats"
        }
    }


@app.get("/health")
async def health_check():
    try:
        stats = retriever.get_retriever_stats()
        
        return {
            "status": "healthy",
            "components": {
                "generator": generator is not None,
                "retriever": retriever is not None,
            },
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    try:
        logger.info(f"Received {len(files)} files for upload")
        
        uploaded_paths = []
        results = []
        
        for file in files:
            ext = Path(file.filename).suffix.lower()
            
            if ext not in settings.allowed_extensions_list:
                raise HTTPException(
                    status_code=400,
                    detail=f"File type {ext} not supported. "
                    f"Allowed: {settings.ALLOWED_EXTENSIONS}"
                )
            
            file_path = settings.upload_path / file.filename
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            uploaded_paths.append(file_path)
            logger.info(f"Uploaded: {file.filename}")
        
        result = retriever.index_documents(uploaded_paths)
        
        return {
            "success": True,
            "files_uploaded": len(files),
            "chunks_indexed": result["chunks_indexed"],
            "embedding_dim": result["embedding_dimension"],
            "files": [f.filename for f in files]
        }
    
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query")
async def query_system(
    query: str = Form(...),
    mode: Optional[str] = Form("both"),
    top_k: Optional[int] = Form(5),
    search_mode: Optional[str] = Form("hybrid"),
    session_id: Optional[str] = Form(None)
):
    try:
        logger.info(f"Processing query: {query} (mode: {mode}, session: {session_id})")
        
        if mode == "use_case":
            result = generator.generate_use_case(query, top_k, search_mode, session_id)
        elif mode == "test_cases":
            result = generator.generate_test_cases(query, top_k, search_mode, session_id)
        elif mode == "both":
            result = generator.generate_combined(query, top_k, search_mode, session_id)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid mode: {mode}. Use: use_case, test_cases, or both"
            )
        
        return result
    
    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    try:
        retriever_stats = retriever.get_retriever_stats()
        generator_stats = generator.get_generator_stats()
        
        return {
            "retriever": retriever_stats,
            "generator": generator_stats
        }
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/index")
async def reset_index():
    try:
        logger.warning("Resetting index...")
        retriever.reset_index()
        
        return {
            "success": True,
            "message": "Index reset successfully"
        }
    except Exception as e:
        logger.error(f"Index reset failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session")
async def create_session():
    """Generates a new session ID for testing."""
    import uuid
    session_id = str(uuid.uuid4())
    logger.info(f"Created new session: {session_id}")
    return {"session_id": session_id}



if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        log_level=settings.LOG_LEVEL
    )
