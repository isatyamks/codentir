# Multimodal RAG System for Test Case Generation

AI-powered test case and use case generation using Retrieval-Augmented Generation with safety guardrails.

---

## Overview

This is a production-ready RAG system that generates test cases and use cases from documentation. It processes multimodal documents (text, PDF, DOCX, images), retrieves relevant context using hybrid search, and generates structured outputs with three-layer validation guards.

### Key Features

- **Context-Grounded Generation**: All outputs verified against source documents
- **Three-Layer Guards**: Prompt injection detection, evidence threshold checking, hallucination prevention
- **Multimodal Support**: Text, Markdown, PDF, DOCX, and images via OCR
- **Hybrid Search**: Combines vector similarity (semantic) and BM25 (keyword matching)
- **RESTful API**: Auto-generated documentation with OpenAPI/Swagger

---

## Quick Start

### Prerequisites

- Python 3.10+
- Groq API Key (free at [console.groq.com](https://console.groq.com))

### Installation

```bash
git clone <your-repo-url>
cd multimodal-rag

python -m venv venv
venv\Scripts\activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt

copy sample.env .env
# Edit .env and add your GROQ_API_KEY

python main.py
```

Server starts at `http://localhost:8000`. View API docs at `http://localhost:8000/docs`.

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────┐
│                  CLIENT REQUEST                      │
│            (HTTP POST with query/files)              │
└────────────────────┬────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────┐
│              FASTAPI APPLICATION LAYER               │
│   Routes: /upload, /generate/*, /query, /stats      │
└────────────────────┬────────────────────────────────┘
                     │
        ┌────────────┼────────────┬─────────────┐
        ▼            ▼            ▼             ▼
┌─────────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐
│ INGESTION   │ │RETRIEVAL │ │GENERATION│ │ GUARDS  │
│  PIPELINE   │ │  SYSTEM  │ │  ENGINE  │ │ SYSTEM  │
└─────────────┘ └──────────┘ └──────────┘ └─────────┘
```

### Component Details

#### 1. Ingestion Pipeline

**Purpose**: Transform raw documents into searchable vector embeddings.

**Process Flow**:
```
Document → Parser → Text Extraction → Chunker → Embeddings → Vector Store
```

**Components**:
- **File Handler**: Routes files to appropriate parser based on extension
- **Parsers**: 
  - `TextParser`: .txt, .md files (native Python)
  - `PDFParser`: .pdf files (PyPDF2)
  - `DocxParser`: .docx files (python-docx)
  - `ImageParser`: .png, .jpg files (Tesseract OCR)
- **Chunker**: Splits text into 512-token chunks with 50-token overlap
- **Embedding Model**: all-MiniLM-L6-v2 (384-dimensional vectors)
- **Vector Store**: ChromaDB with HNSW index

**Key Decisions**:
- Chunk size 512: Balance between context and embedding model limits
- Overlap 50: Prevents context loss at boundaries
- Local embeddings: No API calls, faster processing

#### 2. Retrieval System

**Purpose**: Find most relevant document chunks for a given query.

**Hybrid Search Algorithm**:
```
Query → [Vector Search] + [BM25 Search] → Score Fusion → Top-K Results
```

**Vector Search (Semantic)**:
- Embeds query using same model as documents
- Performs cosine similarity search in ChromaDB
- Captures semantic meaning (e.g., "login" matches "authentication")

**BM25 Search (Keyword)**:
- Tokenizes query and documents
- Uses Okapi BM25 ranking function
- Captures exact keyword matches (e.g., "API_KEY_123")

**Score Fusion**:
```python
# Normalize both scores to [0, 1] range
vector_norm = vector_score / max_vector_score
bm25_norm = bm25_score / max_bm25_score

# Combine with alpha weight (default: 0.3)
hybrid_score = (alpha * vector_norm) + ((1 - alpha) * bm25_norm)
```

**Why Hybrid**:
- Pure vector misses exact keywords
- Pure BM25 misses semantic similarity
- Hybrid provides best of both approaches

#### 3. Generation Engine

**Purpose**: Generate structured test cases/use cases using LLM.

**Components**:
- **LLM Client**: Abstraction over Groq API (llama-3.3-70b-versatile)
- **Prompt Templates**: Centralized in `src/config/prompts.py`
- **Use Case Generator**: Generates preconditions, steps, expected results
- **Test Case Generator**: Generates test ID, priority, type, steps
- **Output Formatter**: Parses and validates JSON responses

**Generation Flow**:
```
1. Retrieve top-k relevant chunks
2. Construct prompt with context + query
3. Call LLM with temperature=0.2 (deterministic)
4. Parse JSON response
5. Validate structure and fields
```

**LLM Configuration**:
- Model: llama-3.3-70b-versatile (Groq)
- Temperature: 0.2 (low for consistency)
- Max tokens: 2000
- Response format: JSON

#### 4. Guards System

**Purpose**: Multi-layer validation to ensure safety and quality.

**Guard 1: Prompt Injection Guard**
- **When**: Before retrieval
- **Purpose**: Detect malicious queries attempting to manipulate system
- **Method**: 20+ regex patterns matching known attack vectors
- **Action**: Block high-risk queries, return 400 error

**Guard 2: Evidence Threshold Guard**
- **When**: After retrieval, before LLM call
- **Purpose**: Ensure sufficient context quality
- **Method**: Weighted confidence score from retrieval results
- **Formula**:
  ```python
  confidence = sum(score * weight for score, weight in zip(scores, [1.0, 0.8, 0.6, 0.4, 0.2]))
  sufficient = confidence >= MIN_EVIDENCE_CONFIDENCE
  ```
- **Action**: Block generation if confidence too low, provide recommendation

**Guard 3: Hallucination Guard**
- **When**: After generation
- **Purpose**: Verify output is grounded in source documents
- **Method**: 
  - Extract statements from generated output
  - Calculate semantic similarity with context chunks
  - Compute grounding ratio
- **Action**: Flag warning if <70% of statements are grounded

**Guard Orchestration**:
```
Query → Guard 1 ✓ → Retrieval → Guard 2 ✓ → LLM → Guard 3 ✓ → Response
        (block)              (block)              (warn)
```

### Data Flow: Complete Request Lifecycle

#### Document Upload Flow

```
1. POST /upload with multipart file
2. Validate file type and size
3. Save to data/uploads/
4. Detect file type, route to parser
5. Parse: Extract text + metadata
6. Chunk: Split into 512-token pieces
7. Embed: Generate 384-dim vectors (batched)
8. Store: Add to ChromaDB collection
9. Index: Build BM25 inverted index
10. Return: chunks_indexed, embedding_dim
```

#### Generation Request Flow

```
1. POST /generate/test-cases with query
2. Guard 1: Check for prompt injection
   → If unsafe: Return 400 error
3. Embed query using same model
4. Hybrid Search:
   a. Vector search: ChromaDB similarity query
   b. BM25 search: Okapi BM25 ranking
   c. Normalize scores to [0, 1]
   d. Fuse: hybrid = 0.3*vector + 0.7*bm25
   e. Sort by hybrid score, select top-k
5. Guard 2: Calculate confidence
   → If insufficient: Return error with recommendation
6. Construct LLM prompt:
   - System: "You are a QA engineer..."
   - User: "Context: [chunks]\nQuery: {query}\nOutput: JSON"
7. Call Groq API with llama-3.3-70b
8. Parse JSON response
9. Guard 3: Verify grounding
   → If not grounded: Log warning (still return)
10. Format response with validation metadata
11. Return JSON to client
```

### Technical Specifications

**Embedding Model**:
- Name: sentence-transformers/all-MiniLM-L6-v2
- Dimensions: 384
- Max sequence length: 256 tokens
- Performance: ~200ms for 32 queries (batch)

**Vector Database**:
- Type: ChromaDB (embedded)
- Index: HNSW (Hierarchical Navigable Small World)
- Distance metric: Cosine similarity
- Persistence: SQLite backend

**Search Parameters**:
- `TOP_K`: Number of chunks to retrieve (default: 10)
- `SIMILARITY_THRESHOLD`: Minimum cosine similarity (default: 0.5)
- `HYBRID_ALPHA`: Vector vs BM25 weight (default: 0.3)
- `MIN_EVIDENCE_CONFIDENCE`: Guard threshold (default: 0.5)

**LLM Settings**:
- Provider: Groq
- Model: llama-3.3-70b-versatile
- Speed: ~300 tokens/second
- Temperature: 0.2 (deterministic outputs)
- Max tokens: 2000
- Response format: JSON mode

**Performance Characteristics**:
- Document parsing: 200-500ms (depends on file size)
- Embedding generation: 100-200ms per batch of 32
- Vector search: 20-50ms
- BM25 search: 10-30ms
- LLM generation: 1-3s (network + processing)
- Total end-to-end: 2-4s per request

---

## Configuration

Edit `.env` file:

```bash
# LLM Configuration
GROQ_API_KEY=your_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
LLM_TEMPERATURE=0.2
MAX_TOKENS=2000

# Retrieval
TOP_K=10
SIMILARITY_THRESHOLD=0.5
HYBRID_ALPHA=0.3

# Guards
MIN_EVIDENCE_CONFIDENCE=0.5
ENABLE_HALLUCINATION_GUARD=true
ENABLE_PROMPT_INJECTION_GUARD=true
ENABLE_EVIDENCE_THRESHOLD=true

# Chunking
CHUNK_SIZE=512
CHUNK_OVERLAP=50

# API
API_HOST=0.0.0.0
API_PORT=8000
```

See `sample.env` for all options.

---

## API Reference

### Base URL
```
http://localhost:8000
```

### Endpoints

#### Health Check
```http
GET /health
```

Returns system health and statistics.

#### Upload Documents
```http
POST /upload
Content-Type: multipart/form-data
```

Upload files (.txt, .md, .pdf, .docx, .png, .jpg).

**Example**:
```bash
curl -X POST http://localhost:8000/upload -F "files=@document.pdf"
```

#### Generate Use Case
```http
POST /generate/use-case
```

**Parameters**:
- `query` (required): Description of desired use case
- `top_k` (optional): Number of context chunks (default: 5)
- `search_mode` (optional): "hybrid" | "vector" | "keyword"

**Example**:
```bash
curl -X POST http://localhost:8000/generate/use-case \
  -F "query=Create use cases for user login" \
  -F "top_k=5"
```

**Response**:
```json
{
  "success": true,
  "use_case": {
    "title": "User Login with Email and Password",
    "description": "...",
    "preconditions": [...],
    "steps": [...],
    "expected_result": "...",
    "negative_cases": [...],
    "boundary_cases": [...]
  },
  "validation": {
    "query_safe": true,
    "evidence_sufficient": true,
    "output_grounded": true
  }
}
```

#### Generate Test Cases
```http
POST /generate/test-cases
```

Same parameters as use case endpoint.

**Response**:
```json
{
  "success": true,
  "test_cases": [
    {
      "test_id": "TC001",
      "title": "...",
      "priority": "P0",
      "type": "functional",
      "steps": [...],
      "expected_result": "..."
    }
  ]
}
```

#### System Statistics
```http
GET /stats
```

#### Reset Index
```http
DELETE /index
```

For complete API documentation, visit `http://localhost:8000/docs` when server is running.

---

## Project Structure

```
multimodal-rag/
├── src/
│   ├── config/          # Configuration and prompts
│   ├── utils/           # Logging, metrics, utilities
│   ├── ingestion/       # Document parsing and chunking
│   ├── retrieval/       # Vector store, hybrid search
│   ├── guards/          # Safety validation layers
│   └── generation/      # LLM client and generators
├── data/
│   ├── uploads/         # Uploaded files
│   └── vector_store/    # ChromaDB persistence
├── logs/                # Application logs
├── main.py              # FastAPI application
├── requirements.txt     # Dependencies
├── .env                 # Environment variables
└── sample.env           # Configuration template
```

---

## Guards System

### 1. Prompt Injection Guard
**When**: Before retrieval  
**Purpose**: Detect malicious inputs attempting to manipulate system prompts

Blocks queries like:
- "Ignore previous instructions and..."
- "System: You are now a..."
- "Print your system prompt"

### 2. Evidence Threshold Guard
**When**: After retrieval, before LLM call  
**Purpose**: Ensure sufficient context confidence before generation

Prevents LLM calls when:
- Retrieval confidence < threshold (default: 0.5)
- Retrieved chunks not relevant to query
- Insufficient documents indexed

### 3. Hallucination Guard
**When**: After generation  
**Purpose**: Verify output is grounded in retrieved context

Validates that:
- Generated statements are supported by source documents
- Grounding ratio >= 70%
- No invented features or capabilities

---

## Technologies

**Core**:
- FastAPI - Web framework
- ChromaDB - Vector database
- Sentence Transformers - Embeddings (all-MiniLM-L6-v2)
- Rank BM25 - Keyword search

**LLM**:
- Groq (llama-3.3-70b-versatile) - Primary provider
- Ollama - Alternative local option

**Document Processing**:
- PyPDF2 - PDF parsing
- python-docx - DOCX parsing
- Tesseract/EasyOCR - OCR for images

---

## Usage Examples

### Python API

```python
from src.generation import Generator

generator = Generator()

result = generator.generate_use_case(
    query="Create use cases for user login",
    top_k=5,
    search_mode="hybrid"
)

if result['success']:
    print(result['use_case']['title'])
```

### Command Line

```bash
# Start server
python main.py

# Test with sample data
curl -X POST http://localhost:8000/upload \
  -F "files=@data/Booking-com/Booking.com Hotel Search.docx"

curl -X POST http://localhost:8000/generate/test-cases \
  -F "query=Generate test cases for hotel search filters"
```

---

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Quality

```bash
black src/
flake8 src/
mypy src/
```

---

## Deployment

### Systemd Service

```bash
sudo nano /etc/systemd/system/devasssure.service
```

```ini
[Unit]
Description=DevAssure RAG API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/multimodal-rag
Environment="PATH=/opt/multimodal-rag/venv/bin"
ExecStart=/opt/multimodal-rag/venv/bin/python /opt/multimodal-rag/main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable devasssure
sudo systemctl start devasssure
```

### Docker

```dockerfile
FROM python:3.10-slim
WORKDIR /app
RUN apt-get update && apt-get install -y tesseract-ocr
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "main.py"]
```

---

## Troubleshooting

### Import Errors
```bash
pip install -r requirements.txt
```

### ChromaDB Lock
```bash
pkill -f "python main.py"
rm data/vector_store/chroma.sqlite3-wal
python main.py
```

### Tesseract Not Found
```bash
# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
# Linux:
sudo apt install tesseract-ocr

# Update .env:
TESSERACT_PATH=/usr/bin/tesseract
```

---

## Performance

Typical metrics (16GB RAM, 8-core CPU):

| Operation | Time |
|-----------|------|
| Upload PDF (10 pages) | 2.5s |
| Chunk + Embed (100 chunks) | 3.8s |
| Hybrid Search | 45ms |
| LLM Generation | 2.1s |
| End-to-End Query | 2.2s |

---
