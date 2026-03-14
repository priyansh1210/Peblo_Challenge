import asyncio
from app.config import get_settings
from app.services.llm_client import get_ollama_client


async def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts using Ollama."""
    settings = get_settings()
    client = get_ollama_client()
    embeddings = []

    for text in texts:
        try:
            result = await asyncio.to_thread(
                client.embed,
                model=settings.OLLAMA_MODEL,
                input=text,
            )
            embeddings.append(result["embeddings"][0])
        except Exception as e:
            print(f"Embedding error: {e}")
            embeddings.append([0.0] * 768)

    return embeddings


async def generate_single_embedding(text: str) -> list[float]:
    """Generate embedding for a single text."""
    results = await generate_embeddings([text])
    return results[0]
