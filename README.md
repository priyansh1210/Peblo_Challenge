# Peblo AI Quiz Engine

AI-powered content ingestion and adaptive quiz generation platform for educational content. Ingests PDFs, extracts and chunks text, generates quiz questions using a local LLM, and adapts difficulty based on student performance.

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

## Features

### Core
- **PDF Ingestion** — Upload educational PDFs, extract text with PyMuPDF, detect metadata (grade, subject) from filenames
- **Smart Chunking** — Sentence-boundary-aware text chunking with configurable size and overlap, automatic topic detection
- **Quiz Generation** — LLM-powered question generation (MCQ, True/False, Fill-in-the-blank) with retry logic
- **Answer Submission** — Submit answers, get instant feedback with correct answer and explanation
- **Adaptive Difficulty** — Automatically adjusts difficulty based on student accuracy (>80% → harder, <40% → easier, requires 3+ answers)

### Optional (All Implemented)
- **Duplicate Detection** — Embedding-based cosine similarity to prevent duplicate questions (threshold: 0.92)
- **Question Validation** — Two-phase: structural validation + LLM quality scoring (min score: 0.4)
- **Embeddings** — Generated via Ollama for both chunks and questions, stored as JSONB
- **Caching** — Redis with automatic in-memory fallback, TTL-based invalidation
- **Quality Evaluation** — LLM rates questions on clarity, correctness, difficulty calibration, and educational value

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

## Setup

### Prerequisites
- Python 3.12+
- PostgreSQL 16+
- Ollama ([ollama.com](https://ollama.com))
- Redis (optional — falls back to in-memory cache)

### Installation

```bash
# Clone and enter project
git clone <repo-url>
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

## API Endpoints

### Health Check
```
GET /health
```

### Ingest PDF
```
POST /ingest
Content-Type: multipart/form-data

file: <PDF file>
```
Returns: document ID, chunk count, extracted metadata

### Generate Quiz
```
POST /generate-quiz
Content-Type: application/json

{
  "document_id": "uuid",
  "num_questions": 5,
  "question_types": ["mcq", "true_false", "fill_blank"],
  "difficulty": "medium"
}
```
Returns: generated questions, duplicate/invalid removal counts

### Retrieve Quiz Questions
```
GET /quiz?document_id=uuid&difficulty=easy&question_type=mcq&topic=math&limit=10
```
All query parameters are optional filters.

### Submit Answer
```
POST /submit-answer
Content-Type: application/json

{
  "student_id": "student-001",
  "question_id": "uuid",
  "selected_answer": "B. 3"
}
```
Returns: correctness, explanation, adaptive difficulty recommendation, student accuracy

## Database Schema

```
source_documents
├── id (UUID, PK)
├── filename, content_hash (unique), grade, subject
├── page_count, created_at

content_chunks
├── id (UUID, PK)
├── document_id (FK → source_documents)
├── chunk_index, text, topic
├── embedding (JSONB)

quiz_questions
├── id (UUID, PK)
├── chunk_id (FK → content_chunks)
├── question_type (mcq/true_false/fill_blank)
├── difficulty (easy/medium/hard)
├── question_text, options (JSONB), correct_answer
├── explanation, embedding (JSONB)
├── quality_score, is_valid

student_answers
├── id (UUID, PK)
├── question_id (FK → quiz_questions)
├── student_id, submitted_answer
├── is_correct, answered_at
```

## Project Structure

```
app/
├── api/            # FastAPI route handlers
│   ├── ingest.py   # PDF upload endpoint
│   ├── quiz.py     # Quiz generation & retrieval
│   └── answer.py   # Answer submission
├── models/         # SQLAlchemy ORM models
│   ├── document.py # SourceDocument
│   ├── chunk.py    # ContentChunk
│   ├── question.py # QuizQuestion
│   └── answer.py   # StudentAnswer
├── schemas/        # Pydantic request/response models
├── services/       # Business logic
│   ├── pdf_extractor.py    # PDF text extraction
│   ├── chunker.py          # Text chunking
│   ├── embedding.py        # Embedding generation
│   ├── quiz_generator.py   # LLM quiz generation
│   ├── question_validator.py # Quality validation
│   ├── duplicate_detector.py # Similarity-based dedup
│   ├── difficulty.py       # Adaptive difficulty
│   ├── scoring.py          # Answer evaluation
│   └── llm_client.py       # Ollama client helper
├── prompts/        # LLM prompt templates
├── cache/          # Redis + fallback cache
├── config.py       # Settings management
├── database.py     # Async DB engine
└── main.py         # FastAPI app factory
```

## Design Decisions

- **Ollama (local LLM)** over cloud APIs — unlimited, free, no API quotas, data stays local
- **JSONB embeddings** instead of pgvector — simpler setup, cosine similarity computed in Python with NumPy
- **Sentence-boundary chunking** — preserves semantic coherence vs. fixed-character splits
- **Two-phase validation** — fast structural checks filter obvious errors before expensive LLM quality scoring
- **Redis with fallback** — graceful degradation if Redis is unavailable
- **CPU-only inference** (`num_gpu: 0`) — works on systems without dedicated GPU VRAM
