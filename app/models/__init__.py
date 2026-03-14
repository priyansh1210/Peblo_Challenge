from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.models.document import SourceDocument
from app.models.chunk import ContentChunk
from app.models.question import QuizQuestion
from app.models.answer import StudentAnswer

__all__ = ["Base", "SourceDocument", "ContentChunk", "QuizQuestion", "StudentAnswer"]
