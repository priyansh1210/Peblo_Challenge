from pydantic import BaseModel
from uuid import UUID


class AnswerSubmitRequest(BaseModel):
    student_id: str
    question_id: UUID
    selected_answer: str


class AnswerSubmitResponse(BaseModel):
    is_correct: bool
    correct_answer: str
    explanation: str | None = None
    new_difficulty: str
    student_accuracy: float
