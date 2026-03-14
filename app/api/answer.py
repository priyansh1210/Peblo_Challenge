from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.question import QuizQuestion
from app.models.answer import StudentAnswer
from app.schemas.answer import AnswerSubmitRequest, AnswerSubmitResponse
from app.services.scoring import evaluate_answer
from app.services.difficulty import resolve_adaptive_difficulty, get_student_accuracy
from app.cache.cache import cache_invalidate

router = APIRouter()


@router.post("/submit-answer", response_model=AnswerSubmitResponse)
async def submit_answer(request: AnswerSubmitRequest, db: AsyncSession = Depends(get_db)):
    """Submit a student answer and get feedback with adaptive difficulty."""

    # Fetch the question
    result = await db.execute(
        select(QuizQuestion).where(QuizQuestion.id == request.question_id)
    )
    question = result.scalar_one_or_none()

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Evaluate the answer
    is_correct = evaluate_answer(question, request.selected_answer)

    # Record the answer
    answer = StudentAnswer(
        question_id=request.question_id,
        student_id=request.student_id,
        submitted_answer=request.selected_answer,
        is_correct=is_correct,
    )
    db.add(answer)
    await db.flush()

    # Get adaptive difficulty
    new_difficulty = await resolve_adaptive_difficulty(
        student_id=request.student_id,
        requested_difficulty=question.difficulty.value,
        db=db,
    )

    # Get student accuracy
    accuracy = await get_student_accuracy(request.student_id, db)

    # Invalidate relevant cache
    await cache_invalidate("quiz:*")

    return AnswerSubmitResponse(
        is_correct=is_correct,
        correct_answer=question.correct_answer,
        explanation=question.explanation,
        new_difficulty=new_difficulty,
        student_accuracy=round(accuracy, 2),
    )
