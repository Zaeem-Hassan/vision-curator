"""Application configuration using Pydantic Settings."""

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Global application settings loaded from environment variables."""

    # ── App ──────────────────────────────────────────────────────────────
    APP_NAME: str = "VisionCurator"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── Database ─────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/visioncurator.db"

    # ── Redis / Celery ───────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ── Storage ──────────────────────────────────────────────────────────
    UPLOAD_DIR: Path = Path("data/uploads")
    FAISS_INDEX_DIR: Path = Path("data/faiss_indices")
    EMBEDDINGS_CACHE_DIR: Path = Path("data/embeddings_cache")

    # ── ML ───────────────────────────────────────────────────────────────
    DEFAULT_MODEL: Literal["dinov2", "simclr", "moco"] = "dinov2"
    DINOV2_VARIANT: Literal["vits14", "vitb14", "vitl14"] = "vitb14"
    EMBEDDING_DIM: int = 768
    BATCH_SIZE: int = 32
    DEVICE: str = "cpu"  # "cuda" if GPU available
    IMAGE_SIZE: int = 224

    # ── Duplicate Detection ──────────────────────────────────────────────
    DUPLICATE_THRESHOLD: float = 0.98

    # ── Clustering ───────────────────────────────────────────────────────
    DEFAULT_CLUSTER_METHOD: Literal["kmeans", "hdbscan"] = "kmeans"
    DEFAULT_N_CLUSTERS: int = 10
    HDBSCAN_MIN_CLUSTER_SIZE: int = 15

    # ── Outlier Detection ────────────────────────────────────────────────
    OUTLIER_CONTAMINATION: float = 0.05
    OUTLIER_KNN_NEIGHBORS: int = 20

    # ── UMAP ─────────────────────────────────────────────────────────────
    UMAP_N_NEIGHBORS: int = 15
    UMAP_MIN_DIST: float = 0.1
    UMAP_N_COMPONENTS: int = 3

    # ── CORS ─────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

# Ensure storage directories exist
for d in [settings.UPLOAD_DIR, settings.FAISS_INDEX_DIR, settings.EMBEDDINGS_CACHE_DIR]:
    d.mkdir(parents=True, exist_ok=True)
