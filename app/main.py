from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine
from app.models import Base
from app.api.ingest import router as ingest_router
from app.api.quiz import router as quiz_router
from app.api.answer import router as answer_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Peblo AI Quiz Engine",
    description="AI-powered content ingestion and adaptive quiz generation platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(ingest_router, tags=["Ingestion"])
app.include_router(quiz_router, tags=["Quiz"])
app.include_router(answer_router, tags=["Answers"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Peblo AI Quiz Engine"}
