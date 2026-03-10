"""VisionCurator — FastAPI Application Entry Point."""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

# Add project root so ML modules are importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings
from app.database import init_db

# ── Pre-import PyTorch at module load time ────────────────────────────────────
# PyTorch must be fully initialised in the MAIN PROCESS before uvicorn spawns
# any threads or worker processes. Importing it here (module level, blocking)
# prevents "partially initialized module / circular import" errors later.
try:
    import torch          # noqa: F401
    import torchvision    # noqa: F401
    logger.info(f"PyTorch {torch.__version__} loaded")
except Exception as _torch_err:
    logger.warning(f"PyTorch import failed at startup: {_torch_err}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — init DB on startup."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down")


def _warmup_torch() -> None:
    """Kept for compatibility — no-op, torch is now imported at module level."""
    pass


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Self-Supervised Dataset Intelligence Platform",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Serve uploaded images ────────────────────────────────────────────────────
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads")

# ── Register Routers ─────────────────────────────────────────────────────────
from app.api.datasets import router as datasets_router
from app.api.embeddings import router as embeddings_router
from app.api.search import router as search_router

app.include_router(datasets_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(embeddings_router, prefix="/api")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/api/dashboard/stats")
async def dashboard_stats():
    """Get dashboard statistics."""
    from sqlalchemy import func, select
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.database import async_session
    from app.models.dataset import Dataset
    from app.models.image import Image

    async with async_session() as db:
        total_datasets = (await db.execute(select(func.count(Dataset.id)))).scalar() or 0
        total_images = (await db.execute(select(func.count(Image.id)))).scalar() or 0
        total_dups = (
            await db.execute(
                select(func.count(Image.id)).where(Image.is_duplicate == True)
            )
        ).scalar() or 0
        total_outliers = (
            await db.execute(
                select(func.count(Image.id)).where(Image.is_outlier == True)
            )
        ).scalar() or 0
        processing = (
            await db.execute(
                select(func.count(Dataset.id)).where(Dataset.status == "processing")
            )
        ).scalar() or 0
        completed = (
            await db.execute(
                select(func.count(Dataset.id)).where(Dataset.status == "completed")
            )
        ).scalar() or 0

        return {
            "total_datasets": total_datasets,
            "total_images": total_images,
            "total_duplicates": total_dups,
            "total_outliers": total_outliers,
            "total_clusters": 0,
            "processing_datasets": processing,
            "completed_datasets": completed,
            "storage_used_mb": 0.0,
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
