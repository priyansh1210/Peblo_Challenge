from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.answer import StudentAnswer
from app.models.question import Difficulty


DIFFICULTY_ORDER = [Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD]


def _next_difficulty(current: Difficulty) -> Difficulty:
    idx = DIFFICULTY_ORDER.index(current)
    return DIFFICULTY_ORDER[min(idx + 1, len(DIFFICULTY_ORDER) - 1)]


def _prev_difficulty(current: Difficulty) -> Difficulty:
    idx = DIFFICULTY_ORDER.index(current)
    return DIFFICULTY_ORDER[max(idx - 1, 0)]


async def resolve_adaptive_difficulty(
    student_id: str,
    requested_difficulty: str,
    db: AsyncSession,
    window_size: int = 10,
) -> str:
    """Adjust difficulty based on student's recent performance.

    Rules:
    - accuracy > 80% over last N answers -> increase difficulty
    - accuracy < 40% over last N answers -> decrease difficulty
    - otherwise -> keep requested difficulty
    """
    result = await db.execute(
        select(StudentAnswer)
        .where(StudentAnswer.student_id == student_id)
        .order_by(StudentAnswer.answered_at.desc())
        .limit(window_size)
    )
    recent_answers = result.scalars().all()

    if len(recent_answers) < 3:
        return requested_difficulty

    correct = sum(1 for a in recent_answers if a.is_correct)
    accuracy = correct / len(recent_answers)

    current = Difficulty(requested_difficulty)

    if accuracy > 0.8:
        return _next_difficulty(current).value
    elif accuracy < 0.4:
        return _prev_difficulty(current).value

    return requested_difficulty


async def get_student_accuracy(student_id: str, db: AsyncSession) -> float:
    """Get overall accuracy for a student."""
    total_result = await db.execute(
        select(func.count(StudentAnswer.id))
        .where(StudentAnswer.student_id == student_id)
    )
    total = total_result.scalar() or 0

    if total == 0:
        return 0.0

    correct_result = await db.execute(
        select(func.count(StudentAnswer.id))
        .where(StudentAnswer.student_id == student_id)
        .where(StudentAnswer.is_correct == True)
    )
    correct = correct_result.scalar() or 0

    return correct / total
