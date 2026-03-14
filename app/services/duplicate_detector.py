import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.question import QuizQuestion
from app.services.embedding import generate_single_embedding
import numpy as np

logger = logging.getLogger(__name__)


async def compute_question_embedding(question: QuizQuestion) -> list[float]:
    """Generate embedding for a question."""
    embed_text = f"{question.question_text} {question.correct_answer}"
    return await generate_single_embedding(embed_text)


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a = np.array(vec1)
    b = np.array(vec2)
    norm_a, norm_b = np.linalg.norm(a), np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


async def check_duplicates(
    questions: list[QuizQuestion],
    db: AsyncSession,
    similarity_threshold: float = 0.92,
) -> tuple[list[QuizQuestion], int]:
    """Filter out duplicate questions using embedding similarity.

    Returns (unique_questions, num_duplicates_removed).
    """
    unique = []
    duplicates_removed = 0

    # Fetch existing question embeddings from DB
    result = await db.execute(
        select(QuizQuestion.embedding).where(QuizQuestion.embedding.isnot(None))
    )
    existing_embeddings = [row[0] for row in result.all()]

    for question in questions:
        try:
            embedding = await compute_question_embedding(question)
            question.embedding = embedding

            # Check against existing questions in DB
            is_dup = False
            for existing_emb in existing_embeddings:
                sim = cosine_similarity(embedding, existing_emb)
                if sim > similarity_threshold:
                    is_dup = True
                    break

            if not is_dup:
                # Check against other questions in the current batch
                for existing_q in unique:
                    if existing_q.embedding is not None:
                        sim = cosine_similarity(embedding, existing_q.embedding)
                        if sim > similarity_threshold:
                            is_dup = True
                            break

            if is_dup:
                duplicates_removed += 1
            else:
                unique.append(question)

        except Exception as e:
            logger.warning(f"Duplicate check error: {e}")
            unique.append(question)

    return unique, duplicates_removed
