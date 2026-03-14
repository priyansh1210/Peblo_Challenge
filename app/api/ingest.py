import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.document import SourceDocument
from app.models.chunk import ContentChunk
from app.schemas.ingestion import IngestResponse
from app.services.pdf_extractor import extract_text_from_pdf, clean_text, detect_metadata
from app.services.chunker import chunk_text, detect_topics
from app.services.embedding import generate_embeddings
from app.utils.hashing import compute_hash
from app.config import get_settings

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
async def ingest_pdf(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """Ingest a PDF file: extract text, chunk it, generate embeddings, and store."""

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    # Check for duplicate document
    content_hash = compute_hash(file_bytes)
    existing = await db.execute(
        select(SourceDocument).where(SourceDocument.content_hash == content_hash)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="This document has already been ingested")

    # Extract text from PDF
    try:
        raw_text, page_count = extract_text_from_pdf(file_bytes)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to extract text from PDF: {e}")

    if not raw_text.strip():
        raise HTTPException(status_code=422, detail="No text content found in PDF")

    cleaned_text = clean_text(raw_text)

    # Detect metadata from filename
    metadata = detect_metadata(file.filename)

    # Create document record
    settings = get_settings()
    document = SourceDocument(
        id=uuid.uuid4(),
        filename=file.filename,
        content_hash=content_hash,
        grade=metadata["grade"],
        subject=metadata["subject"],
        page_count=page_count,
    )
    db.add(document)

    # Chunk the text
    chunks = chunk_text(cleaned_text, chunk_size=settings.CHUNK_SIZE, overlap=settings.CHUNK_OVERLAP)

    # Generate embeddings for all chunks
    embeddings = await generate_embeddings(chunks)

    # Create chunk records
    chunk_records = []
    for i, (chunk_text_str, embedding) in enumerate(zip(chunks, embeddings)):
        topic = detect_topics(chunk_text_str)
        chunk_record = ContentChunk(
            id=uuid.uuid4(),
            document_id=document.id,
            chunk_index=i,
            topic=topic,
            text=chunk_text_str,
            embedding=embedding,
        )
        chunk_records.append(chunk_record)
        db.add(chunk_record)

    await db.flush()

    return IngestResponse(
        document_id=document.id,
        filename=file.filename,
        grade=metadata["grade"],
        subject=metadata["subject"],
        chunk_count=len(chunks),
        message=f"Successfully ingested {file.filename} with {len(chunks)} chunks",
    )
