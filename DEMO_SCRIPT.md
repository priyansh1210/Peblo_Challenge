# DEMO VIDEO SCRIPT — Complete Word-for-Word Guide

**Total Time: ~8-9 minutes**

---

## BEFORE YOU HIT RECORD

Open these windows and arrange them:
- **Terminal** (PowerShell) — left half of screen
- **Postman** — ready to switch to
- **VS Code** — project open, `app/` folder expanded in sidebar
- **Browser** — GitHub repo tab + SAMPLE_OUTPUTS.md tab (raw view)

Run these setup commands in terminal:

```powershell
ollama serve
```
(in a separate terminal if not already running)

```powershell
cd D:\Peblo_Challenge
venv\Scripts\activate
```

Reset the database for a clean demo:
```powershell
python -c "import asyncio; from sqlalchemy import text; from app.database import AsyncSessionLocal; asyncio.run((lambda: AsyncSessionLocal().__aenter__().then(lambda s: s.execute(text('DELETE FROM student_answers')) and s.execute(text('DELETE FROM quiz_questions')) and s.execute(text('DELETE FROM content_chunks')) and s.execute(text('DELETE FROM source_documents')) and s.commit()))())"
```

OR just run this SQL in pgAdmin:
```sql
DELETE FROM student_answers;
DELETE FROM quiz_questions;
DELETE FROM content_chunks;
DELETE FROM source_documents;
```

Now pre-populate the database (so retrieval and answers are instant during recording):

```powershell
uvicorn app.main:app --port 8000
```

In another terminal or Postman:
1. POST /ingest all 3 PDFs
2. POST /generate-quiz for each document (wait for each to finish)
3. Note down:
   - One document_id (for showing in demo)
   - 4 question_ids with their correct_answers (for answer submission demo)
   - Write them on a sticky note next to your screen

Then STOP the server (Ctrl+C). You'll restart it on camera.

**Fill in these before recording:**
```
MATH_DOC_ID     = ___________________________________
QUESTION_1_ID   = ___________________________________
QUESTION_1_ANS  = ___________________________________
QUESTION_2_ID   = ___________________________________
QUESTION_2_ANS  = ___________________________________
QUESTION_3_ID   = ___________________________________
QUESTION_3_ANS  = ___________________________________
QUESTION_4_ID   = ___________________________________
QUESTION_4_ANS  = ___________________________________ (use a WRONG answer here)
```

Set up Postman collection "Peblo Demo" with these pre-saved requests:
1. GET Health — `http://localhost:8000/health`
2. POST Ingest — `http://localhost:8000/ingest` (form-data, file key ready)
3. POST Generate Quiz — `http://localhost:8000/generate-quiz` (JSON body ready)
4. GET Quiz MCQ — `http://localhost:8000/quiz?difficulty=easy&question_type=mcq&limit=3`
5. GET Quiz True/False — `http://localhost:8000/quiz?question_type=true_false`
6. GET Quiz by Document — `http://localhost:8000/quiz?document_id=<MATH_DOC_ID>&limit=3`
7. POST Submit Answer 1 — correct answer body ready
8. POST Submit Answer 2 — correct answer body ready
9. POST Submit Answer 3 — correct answer body ready
10. POST Submit Answer 4 — WRONG answer body ready

**Now hit record on Loom.**

---

## SCENE 1: INTRO (0:00 - 0:30)

**Show:** Browser with GitHub repo (https://github.com/priyansh1210/Peblo_Challenge)

**Say:**

> "Hi, I'm Priyansh. This is my submission for the Peblo AI Backend Engineer Challenge."
>
> "I built a Mini Content Ingestion and Adaptive Quiz Engine. You upload educational PDFs, the system extracts and chunks the content, generates quiz questions using a local LLM, and adapts difficulty based on how the student performs."
>
> "The tech stack is FastAPI, PostgreSQL, and Ollama running Llama 3.2 locally — so there are no API keys or quotas needed. Let me walk you through the code and then do a live demo."

---

## SCENE 2: ARCHITECTURE (0:30 - 2:00)

**Action:** Switch to VS Code. Make sure `app/` folder is expanded in the sidebar.

**Say while clicking on each folder:**

> "The project follows a three-layer architecture — API, Services, and Models."

**Click on `app/api/` to expand it.**

> "The API layer has three route files."

**Click on `ingest.py`.**

> "ingest.py handles PDF uploads."

**Click on `quiz.py`.**

> "quiz.py handles quiz generation and retrieval."

**Click on `answer.py`.**

> "answer.py handles answer submission. These are thin controllers — they validate input and delegate everything to the service layer."

**Click on `app/services/` to expand it.**

> "The services folder is where all the business logic lives. Let me highlight the important ones."

**Click on `pdf_extractor.py`.**

> "pdf_extractor uses PyMuPDF to extract text from PDFs, cleans it up, and detects metadata like grade and subject from the filename using regex patterns."

**Click on `chunker.py`.**

> "The chunker splits text into chunks using sentence-boundary aware splitting — so we never cut a sentence in half. 512-word chunks with 50-word overlap for context continuity. Each chunk also gets a topic detected through keyword matching."

**Click on `quiz_generator.py`.**

> "quiz_generator calls Ollama with a carefully crafted prompt. It includes retry logic because LLMs don't always return perfect JSON — the parser handles markdown code blocks, trailing commas, and truncated output."

**Click on `question_validator.py`.**

> "Two-phase question validation. Phase one is structural — does an MCQ have exactly 4 options? Does a fill-in-the-blank have a blank? Phase two is an LLM quality check — each question gets scored 0 to 1 for clarity, correctness, and educational value. Anything below 0.4 is rejected."

**Click on `duplicate_detector.py`.**

> "Duplicate detection uses cosine similarity on embeddings. If two questions are more than 92% similar, the duplicate gets filtered out. This works both against existing database questions and within the same generated batch."

**Click on `difficulty.py`.**

> "The adaptive difficulty engine. It looks at the student's last 10 answers. If accuracy is above 80%, difficulty goes up — easy to medium to hard. Below 40%, it goes down. It needs at least 3 answers before making any adjustment."

**Click on `app/models/` to expand it.**

> "Four database models — source_documents, content_chunks, quiz_questions, and student_answers. Questions trace back to chunks, chunks trace back to documents — so there's full traceability from any quiz question back to the original PDF content."

**Click on `app/cache/`.**

> "And a caching layer — Redis with an in-memory fallback if Redis isn't running. Quiz retrieval responses are cached for 60 seconds."

**Pause briefly.**

> "I've implemented all the optional nice-to-haves mentioned in the assignment — duplicate detection, question validation with quality scoring, embeddings for similarity, caching, and evaluation logic."

---

## SCENE 3: START THE SERVER (2:00 - 2:30)

**Action:** Switch to Terminal.

**Type:**
```
ollama list
```

**Say:**

> "Ollama is running with Llama 3.2 — 3 billion parameters, about 2 GB on disk."

**Type:**
```
uvicorn app.main:app --port 8000
```

(Server starts — you should see "Uvicorn running on http://127.0.0.1:8000")

> "Server is up."

**Action:** Switch to Postman. Click the pre-saved "GET Health" request. Click Send.

**Say:**

> "Health check confirms everything is running."

(Response shows: `{"status": "healthy", "service": "Peblo AI Quiz Engine"}`)

---

## SCENE 4: INGEST A PDF — LIVE (2:30 - 4:00)

**Action:** In Postman, click the pre-saved "POST Ingest" request.

**Say:**

> "Let's ingest an educational PDF. This is a Grade 1 Math PDF covering numbers, counting, and shapes."

**Action:** In the Body tab, make sure form-data is selected. The file key should already have `peblo_pdf_grade1_math_numbers.pdf` attached. Click **Send**.

(Response appears — takes 2-5 seconds)

> "The response shows a document_id, filename, grade 1, subject Math. Grade and subject were automatically detected from the filename using regex. And it created chunks from the PDF content."

> "Here's what happened behind the scenes — PyMuPDF extracted the text, it was cleaned and normalized, then split into chunks using sentence-boundary aware splitting with overlap. Each chunk got a topic detected via keyword matching, embeddings were generated through Ollama, and everything was stored in PostgreSQL."

**Action:** Click **Send** again (same PDF, same request).

(Response: 409 — `{"detail": "This document has already been ingested"}`)

> "Now watch — I'm uploading the exact same PDF again. And it's rejected — 'This document has already been ingested.' I compute a SHA-256 hash of the file bytes on upload. If we've seen that hash before, it's a duplicate and gets rejected."

---

## SCENE 5: QUIZ GENERATION — SAMPLE OUTPUT (4:00 - 6:00)

**Action:** In Postman, click the pre-saved "POST Generate Quiz" request. Show the request body but DON'T click Send.

**Say:**

> "Now quiz generation. This endpoint takes a document_id, number of questions, question types, and difficulty level."

**Action:** Show the request body:
```json
{
  "document_id": "<MATH_DOC_ID>",
  "num_questions": 10,
  "question_types": ["mcq", "true_false", "fill_blank"],
  "difficulty": "easy"
}
```

> "I'm requesting 10 easy questions — a mix of MCQ, True/False, and Fill-in-the-blank — from the Math PDF we just ingested."

> "Since the LLM runs locally on CPU, generation takes about 30 to 60 seconds. Let me show you a real output that the system produced earlier."

**Action:** Switch to browser tab with SAMPLE_OUTPUTS.md open (or open it in VS Code). Scroll to Section 3: Quiz Generation. Scroll slowly through the response.

> "Here's the actual response. We got 5 high-quality questions back. Let me walk through what happened in the pipeline."

> "The LLM generated 10 questions total. Then duplicate detection kicked in — using cosine similarity on embeddings, 4 questions were flagged as too similar, threshold 0.92, and removed."

> "Then two-phase validation. Every question went through a structural check — does each MCQ have exactly 4 options? Is the correct answer one of them? Then an LLM quality check scored each question from 0 to 1. One question scored below 0.4 and was rejected."

> "So from 10 generated — 4 duplicates removed, 1 invalid removed — we get 5 clean, validated questions."

**Action:** Point at/highlight specific parts as you talk:

> "Look at the first question — 'How many sides does a triangle have?' — MCQ with 4 plausible options, correct answer B. 3, quality score 0.9."

> "This True/False — 'A square has four equal sides' — scored a perfect 1.0."

> "And every question has a source_chunk_id — that's the traceability back to the exact content chunk it was generated from."

---

## SCENE 6: QUIZ RETRIEVAL WITH FILTERS — LIVE (6:00 - 7:00)

**Action:** In Postman, click the pre-saved "GET Quiz MCQ" request. Click **Send**.

**Say:**

> "Now the retrieval API. I can filter questions by difficulty, type, topic, or document. Let me get only easy MCQs."

(Response appears instantly — list of MCQ questions)

> "Instant response — 3 easy MCQs."

**Action:** Click the pre-saved "GET Quiz True/False" request. Click **Send**.

> "Now only True/False questions."

(Response appears instantly)

**Action:** Click the pre-saved "GET Quiz by Document" request. Click **Send**.

> "And filtered by a specific document with a limit."

(Response appears instantly)

> "These responses are cached for 60 seconds — Redis if available, in-memory fallback otherwise. The cache key includes all the filter parameters, so different queries get separately cached results."

---

## SCENE 7: ANSWER SUBMISSION + ADAPTIVE DIFFICULTY — LIVE (7:00 - 8:30)

**Action:** In Postman, click the pre-saved "POST Submit Answer 1" request.

Body should show:
```json
{
  "student_id": "student-001",
  "question_id": "<QUESTION_1_ID>",
  "selected_answer": "<QUESTION_1_ANS>"
}
```

**Say:**

> "Now the student submits an answer. Student-001 is answering a question."

**Action:** Click **Send**.

(Response: `is_correct: true, new_difficulty: easy, student_accuracy: 1.0`)

> "Correct! Accuracy is 1.0. But difficulty is still easy — the adaptive engine needs at least 3 answers before it kicks in."

**Action:** Click the pre-saved "POST Submit Answer 2". Click **Send**.

(Response: `is_correct: true, new_difficulty: easy, student_accuracy: 1.0`)

> "Second correct answer. Still easy — one more."

**Action:** Click the pre-saved "POST Submit Answer 3". Click **Send**.

(Response: `is_correct: true, new_difficulty: medium, student_accuracy: 1.0`)

> "Third correct answer, 100% accuracy — and look at new_difficulty. It jumped from easy to medium! The algorithm checked the last 10 answers, saw accuracy above 80%, and bumped the difficulty up. The progression goes easy, medium, hard."

**Action:** Click the pre-saved "POST Submit Answer 4" (the WRONG answer). Click **Send**.

(Response: `is_correct: false, correct_answer: "...", explanation: "...", student_accuracy: 0.75`)

> "Now a wrong answer. is_correct is false — and notice it shows the correct answer and an explanation, so the student can learn from their mistake. Accuracy dropped to 75%. If they keep getting answers wrong and drop below 40%, the difficulty would go back down to easy."

---

## SCENE 8: DATABASE (8:30 - 9:00)

**Action:** Switch to pgAdmin (or a terminal with psql). Run:

```sql
SELECT 'source_documents' as table_name, count(*) FROM source_documents
UNION ALL SELECT 'content_chunks', count(*) FROM content_chunks
UNION ALL SELECT 'quiz_questions', count(*) FROM quiz_questions
UNION ALL SELECT 'student_answers', count(*) FROM student_answers;
```

**Say:**

> "Quick look at the database — four tables. 3 documents ingested, their content chunks, generated quiz questions, and the student answers we just submitted. Questions link to chunks, chunks link to documents — full traceability chain."

---

## SCENE 9: WRAP UP (9:00 - 9:30)

**Action:** Can stay on the database view or switch back to VS Code/GitHub.

**Say:**

> "To wrap up — this is a complete content ingestion and adaptive quiz engine. It handles PDF extraction with smart chunking, LLM-powered question generation with quality validation and duplicate detection, filtered quiz retrieval with caching, answer submission with scoring, and adaptive difficulty that responds to student performance."
>
> "All optional features from the assignment are implemented. And it runs entirely locally with Ollama — no API costs or rate limits."
>
> "Thank you for reviewing my submission."

**Action:** Stop recording.

---

## QUICK REFERENCE — What's on screen when

| Time | Screen | What's happening |
|------|--------|-----------------|
| 0:00 | Browser (GitHub) | Intro, show repo |
| 0:30 | VS Code | Architecture walkthrough |
| 2:00 | Terminal | ollama list, start server |
| 2:20 | Postman | Health check |
| 2:30 | Postman | Ingest PDF (live) |
| 3:30 | Postman | Duplicate detection (live) |
| 4:00 | Postman → Browser/VS Code | Show generate-quiz request, then sample output |
| 6:00 | Postman | Quiz retrieval with filters (live) |
| 7:00 | Postman | Answer submission x4 (live) |
| 8:30 | pgAdmin/Terminal | Database tables |
| 9:00 | VS Code/GitHub | Wrap up |
