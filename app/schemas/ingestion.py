from pydantic import BaseModel
from uuid import UUID


class IngestResponse(BaseModel):
    document_id: UUID
    filename: str
    grade: int | None
    subject: str | None
    chunk_count: int
    message: str
