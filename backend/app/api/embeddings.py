"""Embedding map API endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.image import Image
from app.models.schemas import EmbeddingMapResponse, EmbeddingPoint

router = APIRouter(prefix="/embeddings", tags=["embeddings"])


@router.get("/map", response_model=EmbeddingMapResponse)
async def get_embedding_map(
    dataset_id: str = Query(..., description="Dataset ID"),
    db: AsyncSession = Depends(get_db),
) -> EmbeddingMapResponse:
    """Return 2D/3D UMAP coordinates for embedding visualization."""
    result = await db.execute(
        select(Image)
        .where(
            Image.dataset_id == dataset_id,
            Image.umap_x.isnot(None),
            Image.umap_y.isnot(None),
        )
        .order_by(Image.created_at)
    )
    images = result.scalars().all()

    points = [
        EmbeddingPoint(
            image_id=img.id,
            filename=img.filename,
            x=img.umap_x or 0.0,
            y=img.umap_y or 0.0,
            z=img.umap_z or 0.0,
            cluster_id=img.cluster_id,
            is_outlier=img.is_outlier,
            is_duplicate=img.is_duplicate,
        )
        for img in images
    ]

    return EmbeddingMapResponse(
        points=points,
        total=len(points),
        dimensions=3,
    )
