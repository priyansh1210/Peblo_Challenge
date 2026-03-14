import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Float, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.models import Base
import enum


class QuestionType(str, enum.Enum):
    MCQ = "mcq"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"


class Difficulty(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chunk_id = Column(UUID(as_uuid=True), ForeignKey("content_chunks.id", ondelete="CASCADE"), nullable=False)
    question_type = Column(Enum(QuestionType), nullable=False)
    difficulty = Column(Enum(Difficulty), nullable=False)
    question_text = Column(Text, nullable=False)
    options = Column(JSONB, nullable=True)
    correct_answer = Column(String, nullable=False)
    explanation = Column(Text, nullable=True)
    embedding = Column(JSONB, nullable=True)  # Store as JSON array
    quality_score = Column(Float, nullable=True)
    is_valid = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    chunk = relationship("ContentChunk", back_populates="questions")
    answers = relationship("StudentAnswer", back_populates="question", cascade="all, delete-orphan")
