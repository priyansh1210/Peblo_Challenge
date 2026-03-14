from ollama import Client
from app.config import get_settings


def get_ollama_client() -> Client:
    """Get Ollama client with configured host."""
    settings = get_settings()
    return Client(host=settings.OLLAMA_BASE_URL)
