import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.models import Base


class ContentChunk(Base):
    __tablename__ = "content_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("source_documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    topic = Column(String, nullable=True)
    text = Column(Text, nullable=False)
    embedding = Column(JSONB, nullable=True)  # Store as JSON array
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("SourceDocument", back_populates="chunks")
    questions = relationship("QuizQuestion", back_populates="chunk", cascade="all, delete-orphan")
