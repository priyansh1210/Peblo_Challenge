from app.models.question import QuizQuestion, QuestionType


def evaluate_answer(question: QuizQuestion, submitted_answer: str) -> bool:
    """Evaluate if a submitted answer is correct."""
    correct = question.correct_answer.strip().lower()
    submitted = submitted_answer.strip().lower()

    if question.question_type == QuestionType.MCQ:
        return submitted == correct

    elif question.question_type == QuestionType.TRUE_FALSE:
        return submitted == correct

    elif question.question_type == QuestionType.FILL_BLANK:
        # Normalize whitespace and compare
        correct_normalized = " ".join(correct.split())
        submitted_normalized = " ".join(submitted.split())
        return submitted_normalized == correct_normalized

    return submitted == correct
