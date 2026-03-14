from pydantic import BaseModel, Field
from uuid import UUID
from app.models.question import QuestionType, Difficulty


class QuizGenerateRequest(BaseModel):
    document_id: UUID
    num_questions: int = Field(default=5, ge=1, le=20)
    question_types: list[str] = ["mcq", "true_false", "fill_blank"]
    difficulty: str = "medium"


class QuestionOut(BaseModel):
    id: UUID
    chunk_id: UUID
    question_type: str
    difficulty: str
    question_text: str
    options: list[str] | None = None
    correct_answer: str
    explanation: str | None = None
    quality_score: float | None = None
    source_chunk_id: str | None = None

    model_config = {"from_attributes": True}


class QuizGenerateResponse(BaseModel):
    questions: list[QuestionOut]
    generated_count: int
    duplicates_removed: int = 0
    invalid_removed: int = 0


class QuizFilter(BaseModel):
    topic: str | None = None
    difficulty: str | None = None
    question_type: str | None = None
    document_id: UUID | None = None
    limit: int = 10
