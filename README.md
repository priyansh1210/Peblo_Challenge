# Peblo AI Quiz Engine

AI-powered content ingestion and adaptive quiz generation platform for educational content. Ingests PDFs, extracts and chunks text, generates quiz questions using a local LLM, and adapts difficulty based on student performance.

## Demo Video

[Watch the demo on Loom](YOUR_LOOM_LINK_HERE)

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  FastAPI     │────▶│  Services    │────▶│  PostgreSQL  │
│  API Layer   │     │  (Business)  │     │  (Storage)   │
└─────────────┘     └──────┬───────┘     └──────────────┘
                           │
                    ┌──────┴───────┐
                    │  Ollama LLM  │
                    │  (Local)     │
                    └──────────────┘
```

**Three-layer separation:**
- **API Layer** (`app/api/`) — Request handling, validation, HTTP responses
- **Service Layer** (`app/services/`) — Business logic, LLM interaction, scoring
- **Data Layer** (`app/models/`) — SQLAlchemy ORM models, database schema

## Data Flow

```
PDF Upload ──▶ PyMuPDF Text Extraction ──▶ Text Cleaning ──▶ Metadata Detection (grade, subject)
    │
    ▼
Sentence-Boundary Chunking (512 words, 50 overlap) ──▶ Topic Detection ──▶ Embedding Generation
    │
    ▼
PostgreSQL Storage (documents, chunks, embeddings)
    │
    ▼
LLM Quiz Generation (prompt + retry) ──▶ Duplicate Detection (cosine similarity > 0.92)
    │
    ▼
Two-Phase Validation (structural + LLM quality ≥ 0.4) ──▶ Valid Questions Stored
    │
    ▼
Student Answers ──▶ Scoring ──▶ Adaptive Difficulty (last 10 answers, >80% ↑, <40% ↓)
```

## Features

### Core
- **PDF Ingestion** — Upload educational PDFs, extract text with PyMuPDF, detect metadata (grade, subject) from filenames, SHA-256 duplicate document detection
- **Smart Chunking** — Sentence-boundary-aware text chunking with configurable size and overlap, automatic topic detection via keyword matching
- **Quiz Generation** — LLM-powered question generation (MCQ, True/False, Fill-in-the-blank) with JSON parsing retry logic
- **Quiz Retrieval** — Filter by difficulty, question type, topic, or document with caching
- **Answer Submission** — Submit answers, get instant feedback with correct answer and explanation
- **Adaptive Difficulty** — Automatically adjusts difficulty based on student accuracy (>80% → harder, <40% → easier, requires 3+ answers)

### Optional (All Implemented)
- **Duplicate Question Detection** — Embedding-based cosine similarity to prevent duplicate questions (threshold: 0.92)
- **Question Validation** — Two-phase: structural validation + LLM quality scoring (min score: 0.4)
- **Embeddings** — Generated via Ollama for both chunks and questions, stored as JSONB
- **Caching** — Redis with automatic in-memory fallback, TTL-based invalidation (60s for quiz retrieval)
- **Quality Evaluation** — LLM rates questions on clarity, correctness, difficulty calibration, and educational value (0.0–1.0)

## Tech Stack

| Component | Technology |
|---|---|
| Backend | Python 3.12+ / FastAPI |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 (async) |
| LLM | Ollama + Llama 3.2:3b (local, free) |
| PDF Parsing | PyMuPDF (fitz) |
| Caching | Redis (with in-memory fallback) |
| Embeddings | Ollama embed API (JSONB storage) |
| Similarity | NumPy cosine similarity |
| Migrations | Alembic |
| Validation | Pydantic v2 |

## Setup

### Prerequisites
- Python 3.12+
- PostgreSQL 16+
- Ollama ([ollama.com](https://ollama.com))
- Redis (optional — falls back to in-memory cache)

### Installation

```bash
# Clone and enter project
git clone https://github.com/priyansh1210/Peblo_Challenge.git
cd Peblo_Challenge

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Pull the LLM model
ollama pull llama3.2:3b

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Create the database
createdb peblo_db  # or via psql: CREATE DATABASE peblo_db;

# Run the server
uvicorn app.main:app --reload --port 8000
```

Tables are created automatically on startup.

### Environment Variables

```env
OLLAMA_MODEL=llama3.2:3b
OLLAMA_BASE_URL=http://localhost:11434
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/peblo_db
REDIS_URL=redis://localhost:6379/0
UPLOAD_DIR=uploads
CHUNK_SIZE=512
CHUNK_OVERLAP=50
```

## API Endpoints

### Health Check
```
GET /health
```
```json
{"status": "healthy", "service": "Peblo AI Quiz Engine"}
```

### Ingest PDF
```
POST /ingest
Content-Type: multipart/form-data

file: <PDF file>
```
- Accepts PDF files up to 10MB
- Detects grade and subject from filename
- Returns document ID, chunk count, extracted metadata
- Returns `409` if document was already ingested (SHA-256 hash check)

### Generate Quiz
```
POST /generate-quiz
Content-Type: application/json

{
  "document_id": "uuid",
  "num_questions": 5,
  "question_types": ["mcq", "true_false", "fill_blank"],
  "difficulty": "easy"
}
```
- `num_questions`: 1–20
- `difficulty`: easy, medium, hard
- Returns generated questions with quality scores, duplicate/invalid removal counts

### Retrieve Quiz Questions
```
GET /quiz?difficulty=easy&question_type=mcq&topic=Shapes&document_id=uuid&limit=10
```
All query parameters are optional filters. Responses are cached for 60 seconds.

### Submit Answer
```
POST /submit-answer
Content-Type: application/json

{
  "student_id": "student-001",
  "question_id": "uuid",
  "selected_answer": "3 sides"
}
```
Returns: correctness, correct answer, explanation, adaptive difficulty recommendation, student accuracy

## Sample Outputs

See [SAMPLE_OUTPUTS.md](SAMPLE_OUTPUTS.md) for real API responses captured from the running system, including:
- PDF ingestion with metadata detection
- Quiz generation with duplicate removal and quality validation stats
- Quiz retrieval with various filters
- Answer submission with adaptive difficulty progression
- Database schema with row counts
- Input validation examples

## Database Schema

```
source_documents
├── id (UUID, PK)
├── filename, content_hash (unique), grade, subject
├── page_count, created_at

content_chunks
├── id (UUID, PK)
├── document_id (FK → source_documents, CASCADE)
├── chunk_index, text, topic
├── embedding (JSONB), created_at

quiz_questions
├── id (UUID, PK)
├── chunk_id (FK → content_chunks, CASCADE)
├── question_type (mcq / true_false / fill_blank)
├── difficulty (easy / medium / hard)
├── question_text, options (JSONB), correct_answer
├── explanation, embedding (JSONB)
├── quality_score (0.0–1.0), is_valid, created_at

student_answers
├── id (UUID, PK)
├── question_id (FK → quiz_questions, CASCADE)
├── student_id, submitted_answer
├── is_correct, answered_at
```

**Traceability chain:** `student_answers → quiz_questions → content_chunks → source_documents`

## Project Structure

```
app/
├── api/                        # FastAPI route handlers
│   ├── ingest.py               # POST /ingest
│   ├── quiz.py                 # POST /generate-quiz, GET /quiz
│   └── answer.py               # POST /submit-answer
├── models/                     # SQLAlchemy ORM models
│   ├── document.py             # SourceDocument
│   ├── chunk.py                # ContentChunk
│   ├── question.py             # QuizQuestion + enums
│   └── answer.py               # StudentAnswer
├── schemas/                    # Pydantic request/response models
│   ├── ingestion.py            # IngestResponse
│   ├── quiz.py                 # QuizGenerateRequest/Response, QuestionOut
│   └── answer.py               # AnswerSubmitRequest/Response
├── services/                   # Business logic
│   ├── pdf_extractor.py        # PDF text extraction + cleaning + metadata
│   ├── chunker.py              # Sentence-boundary chunking + topic detection
│   ├── embedding.py            # Ollama embedding generation
│   ├── quiz_generator.py       # LLM quiz generation + JSON parsing + retry
│   ├── question_validator.py   # Structural + LLM quality validation
│   ├── duplicate_detector.py   # Cosine similarity deduplication
│   ├── difficulty.py           # Adaptive difficulty engine
│   ├── scoring.py              # Answer evaluation
│   └── llm_client.py           # Ollama client setup
├── prompts/                    # LLM prompt templates
│   └── quiz_prompts.py         # Generation + validation prompts
├── cache/                      # Caching layer
│   └── cache.py                # Redis + in-memory fallback
├── utils/
│   └── hashing.py              # SHA-256 for document dedup
├── config.py                   # Pydantic settings from .env
├── database.py                 # Async SQLAlchemy engine + session
└── main.py                     # FastAPI app factory + lifespan
```

## Design Decisions

| Decision | Rationale |
|---|---|
| **Ollama (local LLM)** | Unlimited, free, no API quotas, data stays local |
| **Llama 3.2:3b** | Small enough to run on CPU, fast inference for a demo |
| **JSONB embeddings** | Simpler than pgvector, cosine similarity computed in Python with NumPy |
| **Sentence-boundary chunking** | Preserves semantic coherence vs. fixed-character splits |
| **Two-phase validation** | Fast structural checks filter obvious errors before expensive LLM quality scoring |
| **Redis with fallback** | Graceful degradation if Redis is unavailable |
| **Async SQLAlchemy** | Non-blocking DB I/O, better concurrency |
| **SHA-256 document hashing** | Efficient duplicate document detection without re-parsing |
| **CPU-only inference** | Works on systems without dedicated GPU |
| **Retry logic (3 attempts)** | Handles LLM JSON parsing failures gracefully |
