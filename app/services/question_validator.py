import json
import re
import asyncio

from app.config import get_settings
from app.services.llm_client import get_ollama_client
from app.models.question import QuizQuestion, QuestionType
from app.prompts.quiz_prompts import build_validation_prompt


def structural_validation(question: QuizQuestion) -> tuple[bool, str]:
    """Validate question structure. Returns (is_valid, reason)."""
    if not question.question_text or len(question.question_text.strip()) < 10:
        return False, "Question text too short"

    if not question.correct_answer or len(question.correct_answer.strip()) == 0:
        return False, "Missing correct answer"

    if question.question_type == QuestionType.MCQ:
        if not question.options or len(question.options) != 4:
            return False, "MCQ must have exactly 4 options"
        if question.correct_answer not in question.options:
            return False, "Correct answer not in options"

    elif question.question_type == QuestionType.TRUE_FALSE:
        if question.correct_answer not in ["True", "False"]:
            return False, "True/False answer must be 'True' or 'False'"

    elif question.question_type == QuestionType.FILL_BLANK:
        if "___" not in question.question_text:
            return False, "Fill-in-the-blank must contain '___'"

    return True, "Valid"


async def llm_quality_check(question: QuizQuestion) -> float:
    """Use Ollama to evaluate question quality. Returns score 0.0-1.0."""
    settings = get_settings()

    prompt = build_validation_prompt(
        question_text=question.question_text,
        question_type=question.question_type.value,
        options=question.options,
        correct_answer=question.correct_answer,
    )

    try:
        client = get_ollama_client()
        response = await asyncio.to_thread(
            client.chat,
            model=settings.OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.3, "num_predict": 256, "num_gpu": 0},
        )
        text = response["message"]["content"].strip()

        match = re.search(r'\{[\s\S]*?\}', text)
        if match:
            result = json.loads(match.group())
            return float(result.get("quality_score", 0.5))
    except Exception as e:
        print(f"Quality check error: {e}")

    return 0.5


async def validate_questions(
    questions: list[QuizQuestion],
    min_quality_score: float = 0.4,
) -> tuple[list[QuizQuestion], int]:
    """Validate a batch of questions. Returns (valid_questions, num_invalid)."""
    valid = []
    invalid_count = 0

    for question in questions:
        # Phase 1: Structural validation
        is_valid, reason = structural_validation(question)
        if not is_valid:
            question.is_valid = False
            question.quality_score = 0.0
            invalid_count += 1
            continue

        # Phase 2: LLM quality check
        score = await llm_quality_check(question)
        question.quality_score = score
        question.is_valid = score >= min_quality_score

        if question.is_valid:
            valid.append(question)
        else:
            invalid_count += 1

    return valid, invalid_count
