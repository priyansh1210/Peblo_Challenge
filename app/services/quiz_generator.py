import json
import re
import uuid
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import get_settings
from app.services.llm_client import get_ollama_client
from app.models.chunk import ContentChunk
from app.models.document import SourceDocument
from app.models.question import QuizQuestion, QuestionType, Difficulty
from app.prompts.quiz_prompts import build_quiz_prompt


def _fix_json_string(text: str) -> str:
    """Attempt to fix common JSON issues from LLM output."""
    # Remove trailing commas before ] or }
    text = re.sub(r',\s*([}\]])', r'\1', text)
    # Fix unescaped newlines inside strings
    text = re.sub(r'(?<=": ")(.*?)(?=")', lambda m: m.group().replace('\n', '\\n'), text)
    return text


def _parse_json_response(text: str) -> list[dict]:
    """Parse JSON from LLM response, handling markdown code blocks."""
    text = text.strip()
    match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if match:
        text = match.group(1).strip()
    # Try to find JSON array
    arr_match = re.search(r'\[[\s\S]*\]', text)
    if arr_match:
        text = arr_match.group()
    # First try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try fixing common issues
    try:
        return json.loads(_fix_json_string(text))
    except json.JSONDecodeError:
        pass
    # Try parsing individual objects if array is truncated
    objects = []
    for obj_match in re.finditer(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text):
        try:
            obj = json.loads(_fix_json_string(obj_match.group()))
            if "question_text" in obj:
                objects.append(obj)
        except json.JSONDecodeError:
            continue
    if objects:
        return objects
    raise json.JSONDecodeError("Could not parse any valid questions", text, 0)


def _has_bare_letter_options(options: list | None) -> bool:
    """Check if MCQ options are just bare letters like ['A', 'B', 'C', 'D']."""
    if not options:
        return False
    return all(len(opt.strip()) <= 2 for opt in options)


def _map_question_type(type_str: str) -> QuestionType:
    mapping = {
        "mcq": QuestionType.MCQ,
        "true_false": QuestionType.TRUE_FALSE,
        "fill_blank": QuestionType.FILL_BLANK,
    }
    return mapping.get(type_str.lower(), QuestionType.MCQ)


def _map_difficulty(diff_str: str) -> Difficulty:
    mapping = {
        "easy": Difficulty.EASY,
        "medium": Difficulty.MEDIUM,
        "hard": Difficulty.HARD,
    }
    return mapping.get(diff_str.lower(), Difficulty.MEDIUM)


async def generate_quiz_questions(
    document_id: uuid.UUID,
    num_questions: int,
    question_types: list[str],
    difficulty: str,
    db: AsyncSession,
) -> list[QuizQuestion]:
    """Generate quiz questions for a document using Ollama."""
    settings = get_settings()

    # Fetch chunks for the document
    result = await db.execute(
        select(ContentChunk)
        .where(ContentChunk.document_id == document_id)
        .order_by(ContentChunk.chunk_index)
    )
    chunks = result.scalars().all()
    if not chunks:
        raise ValueError("No content chunks found for this document")

    # Fetch document for grade info
    doc_result = await db.execute(
        select(SourceDocument).where(SourceDocument.id == document_id)
    )
    document = doc_result.scalar_one_or_none()

    # Combine chunk texts for context
    context = "\n\n".join([chunk.text for chunk in chunks])
    if len(context) > 6000:
        context = context[:6000]

    # Build prompt and call Ollama
    prompt = build_quiz_prompt(
        context=context,
        num_questions=num_questions,
        question_types=question_types,
        difficulty=difficulty,
        grade=document.grade if document else None,
    )

    # Retry logic for JSON parsing
    raw_questions = None
    for attempt in range(3):
        try:
            client = get_ollama_client()
            response = await asyncio.to_thread(
                client.chat,
                model=settings.OLLAMA_MODEL,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.7, "num_predict": 4096, "num_gpu": 0},
            )
            raw_questions = _parse_json_response(response["message"]["content"])
            break
        except (json.JSONDecodeError, Exception) as e:
            if attempt == 2:
                raise ValueError(f"Failed to generate valid quiz after 3 attempts: {e}")

    # Map to QuizQuestion models, filtering out bare-letter MCQ options
    questions = []
    for i, q_data in enumerate(raw_questions):
        chunk = chunks[i % len(chunks)]
        q_type = _map_question_type(q_data.get("type", "mcq"))
        options = q_data.get("options")

        # Skip MCQs where the LLM returned bare letters instead of full-text options
        if q_type == QuestionType.MCQ and _has_bare_letter_options(options):
            continue

        question = QuizQuestion(
            id=uuid.uuid4(),
            chunk_id=chunk.id,
            question_type=q_type,
            difficulty=_map_difficulty(q_data.get("difficulty", difficulty)),
            question_text=q_data["question_text"],
            options=options,
            correct_answer=q_data["correct_answer"],
            explanation=q_data.get("explanation"),
        )
        questions.append(question)

    return questions
