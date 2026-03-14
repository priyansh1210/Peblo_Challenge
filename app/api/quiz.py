import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.database import get_db
from app.models.question import QuizQuestion, QuestionType, Difficulty
from app.models.chunk import ContentChunk
from app.schemas.quiz import QuizGenerateRequest, QuizGenerateResponse, QuestionOut
from app.services.quiz_generator import generate_quiz_questions
from app.services.duplicate_detector import check_duplicates
from app.services.question_validator import validate_questions
from app.cache.cache import cache_get, cache_set, cache_invalidate

logger = logging.getLogger(__name__)
router = APIRouter()

VALID_DIFFICULTIES = {"easy", "medium", "hard"}
VALID_QUESTION_TYPES = {"mcq", "true_false", "fill_blank"}


def _question_to_out(q: QuizQuestion) -> QuestionOut:
    return QuestionOut(
        id=q.id,
        chunk_id=q.chunk_id,
        question_type=q.question_type.value,
        difficulty=q.difficulty.value,
        question_text=q.question_text,
        options=q.options,
        correct_answer=q.correct_answer,
        explanation=q.explanation,
        quality_score=q.quality_score,
        source_chunk_id=str(q.chunk_id),
    )


@router.post("/generate-quiz", response_model=QuizGenerateResponse)
async def generate_quiz(request: QuizGenerateRequest, db: AsyncSession = Depends(get_db)):
    """Generate quiz questions from an ingested document."""

    # Validate inputs
    if request.num_questions < 1 or request.num_questions > 20:
        raise HTTPException(status_code=400, detail="num_questions must be between 1 and 20")

    if request.difficulty not in VALID_DIFFICULTIES:
        raise HTTPException(status_code=400, detail=f"difficulty must be one of: {VALID_DIFFICULTIES}")

    invalid_types = set(request.question_types) - VALID_QUESTION_TYPES
    if invalid_types:
        raise HTTPException(status_code=400, detail=f"Invalid question types: {invalid_types}")

    # Generate questions using LLM
    try:
        questions = await generate_quiz_questions(
            document_id=request.document_id,
            num_questions=request.num_questions,
            question_types=request.question_types,
            difficulty=request.difficulty,
            db=db,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Quiz generation failed: {e}")
        raise HTTPException(status_code=500, detail="Quiz generation failed. Please try again.")

    total_generated = len(questions)

    # Duplicate detection
    unique_questions, duplicates_removed = await check_duplicates(questions, db)

    # Question validation
    valid_questions, invalid_removed = await validate_questions(unique_questions)

    # Persist valid questions
    for q in valid_questions:
        db.add(q)
    await db.flush()

    # Invalidate quiz cache
    await cache_invalidate("quiz:*")

    return QuizGenerateResponse(
        questions=[_question_to_out(q) for q in valid_questions],
        generated_count=total_generated,
        duplicates_removed=duplicates_removed,
        invalid_removed=invalid_removed,
    )


@router.get("/quiz", response_model=list[QuestionOut])
async def get_quiz(
    topic: str | None = Query(None),
    difficulty: str | None = Query(None),
    question_type: str | None = Query(None),
    document_id: UUID | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve quiz questions with optional filters."""

    # Check cache
    cache_key = f"quiz:{topic}:{difficulty}:{question_type}:{document_id}:{limit}"
    cached = await cache_get(cache_key)
    if cached:
        return [QuestionOut(**q) for q in cached]

    # Build query
    query = select(QuizQuestion).where(QuizQuestion.is_valid == True)

    if difficulty:
        if difficulty not in VALID_DIFFICULTIES:
            raise HTTPException(status_code=400, detail=f"difficulty must be one of: {VALID_DIFFICULTIES}")
        query = query.where(QuizQuestion.difficulty == Difficulty(difficulty))

    if question_type:
        if question_type not in VALID_QUESTION_TYPES:
            raise HTTPException(status_code=400, detail=f"question_type must be one of: {VALID_QUESTION_TYPES}")
        query = query.where(QuizQuestion.question_type == QuestionType(question_type))

    if document_id:
        query = query.join(ContentChunk).where(ContentChunk.document_id == document_id)

    if topic:
        if not document_id:
            query = query.join(ContentChunk)
        query = query.where(ContentChunk.topic.ilike(f"%{topic}%"))

    query = query.limit(limit)

    result = await db.execute(query)
    questions = result.scalars().all()

    output = [_question_to_out(q) for q in questions]

    # Cache the result
    await cache_set(cache_key, [q.model_dump(mode="json") for q in output], ttl=60)

    return output
