# DevAssure - Multimodal RAG System for Test Case Generation

**AI-Powered Test Case & Use Case Generation using Retrieval-Augmented Generation**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Examples](#examples)
- [Project Structure](#project-structure)
- [Technologies](#technologies)
- [Development Tools](#development-tools)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## 📖 Overview

DevAssure is a **production-ready Retrieval-Augmented Generation (RAG) system** designed to automatically generate **high-quality test cases and use cases** from multimodal documents. The system ingests various document types, retrieves relevant context using hybrid search, and generates structured outputs with comprehensive safety guardrails.

### Why DevAssure?

- **🎯 Context-Grounded**: Never invents features - all outputs based on actual documents
- **🛡️ Safety-First**: 3-layer guard system prevents hallucinations and prompt injections
- **📄 Multimodal**: Handles Text, Markdown, PDF, DOCX, and Images (OCR)
- **⚡ Fast**: Hybrid search (vector + keyword) with configurable thresholds
- **🔌 API-First**: RESTful API with auto-generated documentation
- **🎨 Flexible**: Supports multiple LLM providers (Groq, OpenAI, Anthropic, Ollama)

---

## ✨ Features

### Document Processing
- ✅ **4 File Types**: Text/Markdown, PDF, DOCX, Images (PNG/JPG)
- ✅ **Smart Chunking**: 3 strategies (sliding window, sentence-based, paragraph-based)
- ✅ **OCR Support**: Tesseract and EasyOCR for image text extraction
- ✅ **Metadata Preservation**: Source tracking and attribution

### Retrieval System
- ✅ **Hybrid Search**: Vector similarity (sentence-transformers) + BM25 keyword search
- ✅ **384-dim Embeddings**: Local model (all-MiniLM-L6-v2) or OpenAI
- ✅ **Persistent Storage**: ChromaDB for efficient vector operations
- ✅ **Reranking**: Optional cross-encoder for improved relevance

### Generation Engine
- ✅ **Use Case Generation**: Structured use cases with preconditions, steps, expected results
- ✅ **Test Case Generation**: Positive, negative, and boundary test cases
- ✅ **Multi-Provider LLM**: Groq (free!), OpenAI, Anthropic, Ollama
- ✅ **JSON Output**: Validated, structured responses

### Safety Guards (High Priority!)
- ✅ **Hallucination Prevention**: Context grounding verification (70% threshold)
- ✅ **Evidence Threshold**: Minimum confidence checks before generation
- ✅ **Prompt Injection Protection**: 20+ malicious pattern detection
- ✅ **Orchestrated Pipeline**: Multi-layer validation

### API & Observability
- ✅ **8 REST Endpoints**: Upload, query, generate, stats, health
- ✅ **Auto Documentation**: Swagger UI + ReDoc
- ✅ **Comprehensive Logging**: Colored console + rotating file logs
- ✅ **Performance Metrics**: Latency, token usage, counters

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT REQUEST                           │
│                    (Upload / Query / Generate)                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI LAYER (main.py)                     │
│  Routes: /upload, /query, /generate/*, /health, /stats          │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐   ┌──────────────────┐   ┌──────────────┐
│  INGESTION   │   │    RETRIEVAL     │   │  GENERATION  │
│   PIPELINE   │   │     SYSTEM       │   │    ENGINE    │
├──────────────┤   ├──────────────────┤   ├──────────────┤
│ • Parsers    │   │ • Embeddings     │   │ • LLM Client │
│   - Text     │   │ • Vector Store   │   │ • Use Cases  │
│   - PDF      │──▶│ • Hybrid Search  │──▶│ • Test Cases │
│   - DOCX     │   │ • Reranking      │   │ • Formatter  │
│   - Images   │   │                  │   │              │
│ • Chunker    │   │                  │   │              │
└──────────────┘   └──────────────────┘   └──────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      GUARD ORCHESTRATOR                          │
│  ┌───────────────┬────────────────────┬─────────────────────┐  │
│  │ Prompt        │ Evidence           │ Hallucination       │  │
│  │ Injection     │ Threshold          │ Guard               │  │
│  │ Guard         │ Guard              │                     │  │
│  └───────────────┴────────────────────┴─────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  JSON RESPONSE  │
                    │  (Validated)    │
                    └─────────────────┘
```

### Data Flow

1. **Document Upload** → Parse → Chunk → Embed → Store in ChromaDB
2. **User Query** → Guard Check → Retrieve Top-K → Evidence Check
3. **LLM Generation** → Parse JSON → Hallucination Check → Return

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Git
- Groq API Key (free at [console.groq.com](https://console.groq.com))

### 1-Minute Setup

```bash
# Clone repository
git clone <your-repo-url>
cd devasssure

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env and add your GROQ_API_KEY

# Start the API server
python main.py
```

Server starts at: **http://localhost:8000**

Interactive docs: **http://localhost:8000/docs**

---

## 📦 Installation

### Detailed Setup

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd devasssure

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Set up environment variables
copy .env.example .env

# 6. Get Groq API Key
# Visit: https://console.groq.com
# Sign up (free, no credit card)
# Create API key
# Add to .env: GROQ_API_KEY=gsk_your_key_here

# 7. (Optional) For OCR support
# Install Tesseract: https://github.com/tesseract-ocr/tesseract
# Or set USE_EASYOCR=true in .env
```

---

## ⚙️ Configuration

Edit `.env` file to customize:

```bash
# LLM Provider (choose one)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# Retrieval Settings
TOP_K=5                         # Number of chunks to retrieve
SIMILARITY_THRESHOLD=0.7        # Min similarity score (0-1)
HYBRID_ALPHA=0.5               # Vector vs keyword weight

# Guard Settings
MIN_EVIDENCE_CONFIDENCE=0.65    # Min score to generate (0-1)
ENABLE_HALLUCINATION_GUARD=true
ENABLE_PROMPT_INJECTION_GUARD=true
ENABLE_EVIDENCE_THRESHOLD=true

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
MAX_FILE_SIZE=10485760         # 10MB

# Chunking
CHUNK_SIZE=512
CHUNK_OVERLAP=50
MIN_CHUNK_SIZE=100
```

See `.env.example` for all available options.

---

## 💻 Usage

### Option 1: Run API Server

```bash
# Start server
python main.py

# Or use the batch script
run_api.bat
```

### Option 2: Python API

```python
from src.generation import Generator

# Initialize
generator = Generator()

# Generate use case
result = generator.generate_use_case(
    query="Create use cases for user login",
    top_k=5,
    search_mode="hybrid"
)

if result['success']:
    print(result['use_case']['title'])
    print(result['use_case']['steps'])
```

### Option 3: CLI Scripts

```bash
# Test Phase 5 (Generation)
python scripts\test_phase5_quick.py

# Interactive testing
python scripts\interactive_test_phase5.py

# API testing
python scripts\test_api.py
```

---

## 📡 API Documentation

### Base URL
```
http://localhost:8000
```

### Endpoints

#### 1. Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "components": {
    "generator": true,
    "retriever": true
  },
  "statistics": {
    "total_documents": 8,
    "queries_processed": 5
  }
}
```

#### 2. Upload Documents
```http
POST /upload
Content-Type: multipart/form-data
```

**Body:**
- `files`: File(s) to upload (.txt, .md, .pdf, .docx, .png, .jpg)

**Response:**
```json
{
  "success": true,
  "files_uploaded": 1,
  "chunks_indexed": 8,
  "embedding_dim": 384,
  "files": ["document.pdf"]
}
```

#### 3. Generate Use Case
```http
POST /generate/use-case
Content-Type: application/x-www-form-urlencoded
```

**Body:**
- `query`: User query (required)
- `top_k`: Number of chunks (default: 5)
- `search_mode`: "hybrid" | "vector" | "keyword" (default: "hybrid")

**Response:**
```json
{
  "success": true,
  "use_case": {
    "title": "User Login with Email Verification",
    "description": "...",
    "preconditions": [...],
    "steps": [...],
    "expected_result": "...",
    "negative_cases": [...],
    "boundary_cases": [...]
  },
  "tokens": {"total": 450},
  "validation": {
    "query_safe": true,
    "evidence_sufficient": true,
    "output_grounded": true
  }
}
```

#### 4. Generate Test Cases
```http
POST /generate/test-cases
```

Same format as use case endpoint.

#### 5. General Query
```http
POST /query
```

**Body:**
- `query`: User query
- `mode`: "use_case" | "test_cases" | "both"
- `top_k`: Number of chunks
- `search_mode`: Search mode

#### 6. System Statistics
```http
GET /stats
```

#### 7. Reset Index
```http
DELETE /index
```

### Interactive Documentation

Visit **http://localhost:8000/docs** for full Swagger UI documentation with request/response examples and try-it-yourself interface.

---

## 📚 Examples

### Example 1: Upload and Query

```bash
# 1. Upload document
curl -X POST http://localhost:8000/upload \
  -F "files=@docs/dashboard.txt"

# 2. Generate use case
curl -X POST http://localhost:8000/generate/use-case \
  -F "query=Create use cases for dashboard zoom feature" \
  -F "top_k=5"
```

### Example 2: Python Client

```python
import requests

# Upload
files = {'files': open('docs/dashboard.txt', 'rb')}
response = requests.post('http://localhost:8000/upload', files=files)
print(response.json())

# Generate
data = {'query': 'Generate test cases for user roles', 'top_k': 5}
response = requests.post('http://localhost:8000/generate/test-cases', data=data)
result = response.json()

if result['success']:
    for tc in result['test_cases']:
        print(f"{tc['test_id']}: {tc['title']}")
```

### Example 3: With Sample Data

```bash
# Use provided Booking.com data
curl -X POST http://localhost:8000/upload \
  -F "files=@data/Booking-com/Booking.com Hotel Search.docx"

curl -X POST http://localhost:8000/generate/use-case \
  -F "query=Create use cases for hotel search filters"
```

---

## 📁 Project Structure

```
devasssure/
├── src/                          # Source code
│   ├── config/                   # Configuration & settings
│   ├── utils/                    # Utilities
│   ├── ingestion/               # Document ingestion
│   ├── retrieval/               # Retrieval system
│   ├── guards/                   # Safety guards
│   └── generation/              # Generation engine
├── tests/                        # Unit tests
├── scripts/                      # Utility scripts
├── docs/                         # Documentation & sample data
├── data/                         # Data storage
│   ├── Booking-com/             # Sample Booking.com data
│   ├── uploads/                 # Uploaded files
│   └── vector_store/            # ChromaDB storage
├── logs/                         # Application logs
├── main.py                       # FastAPI application
├── run_api.bat                   # Server start script
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template
└── README.md                     # This file
```

---

## 🔧 Technologies

### Core
- **FastAPI** - Modern web framework
- **LangChain** - RAG framework
- **ChromaDB** - Vector database
- **Sentence Transformers** - Embeddings

### LLM Providers
- **Groq** - Fast, free (primary)
- **OpenAI, Anthropic, Ollama** - Supported

### Testing
- **pytest, black, flake8, mypy**

---

## 🛠️ Development Tools

### IDEs Used
- **Visual Studio Code** - Primary
- **Cursor AI** - AI assistance
- **PyCharm** - Alternative

---

## 🧪 Testing

```bash
# All phases
pytest tests/ -v

# Individual phases
python scripts\validate_phase*.py

# API tests
python scripts\test_api.py
```

---

## 🔧 Troubleshooting

### Common Issues

1. **Import Errors**: `pip install -r requirements.txt`
2. **API Key Not Found**: Check `.env` file
3. **ChromaDB Issues**: Delete `data/vector_store/*`
4. **Port in Use**: Change `API_PORT` in `.env`

---

## 📄 License

MIT License

---

## 👥 Author

DevAssure AI Engineer Intern Assignment

---

**Built with ❤️ using Python, FastAPI, and modern RAG techniques**

🚀 **Ready for Production** | 🛡️ **Safety-First** | 📊 **Data-Driven** | ⚡ **High Performance**
