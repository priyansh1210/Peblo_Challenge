import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models import Base


class SourceDocument(Base):
    __tablename__ = "source_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String, nullable=False)
    content_hash = Column(String, unique=True, nullable=False)
    grade = Column(Integer, nullable=True)
    subject = Column(String, nullable=True)
    page_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    chunks = relationship("ContentChunk", back_populates="document", cascade="all, delete-orphan")
