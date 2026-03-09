"""Search API endpoints."""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Query, UploadFile
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.image import Image
from app.models.schemas import ImageResponse, SimilaritySearchResponse

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/similar", response_model=SimilaritySearchResponse)
async def similarity_search(
    dataset_id: str = Query(..., description="Dataset to search within"),
    file: UploadFile = File(...),
    top_k: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> SimilaritySearchResponse:
    """Search for similar images by uploading a query image."""
    import numpy as np

    from ml.embedding_models.dinov2 import DINOv2Model
    from ml.embeddings.faiss_index import FAISSIndex
    from ml.preprocessing.preprocessing import preprocess_single_image

    # Save query image temporarily
    tmp_path = Path(f"/tmp/{uuid.uuid4()}.jpg")
    content = await file.read()
    with open(tmp_path, "wb") as f:
        f.write(content)

    try:
        # Compute embedding for query
        model = DINOv2Model(variant=settings.DINOV2_VARIANT, device=settings.DEVICE)
        image_tensor = preprocess_single_image(str(tmp_path), settings.IMAGE_SIZE)
        query_embedding = model.extract_single(image_tensor)

        # Load FAISS index
        index_path = settings.FAISS_INDEX_DIR / f"{dataset_id}.index"
        if not index_path.exists():
            return SimilaritySearchResponse(
                query_image=file.filename, results=[], distances=[]
            )

        faiss_index = FAISSIndex(dim=settings.EMBEDDING_DIM)
        faiss_index.load(str(index_path))

        # Search
        distances, indices = faiss_index.search(query_embedding.reshape(1, -1), top_k)

        # Map indices to images
        result = await db.execute(
            select(Image)
            .where(Image.dataset_id == dataset_id, Image.has_embedding == True)
            .order_by(Image.created_at)
        )
        all_images = result.scalars().all()

        matched_images = []
        matched_distances = []
        for dist, idx in zip(distances[0], indices[0]):
            if 0 <= idx < len(all_images):
                matched_images.append(ImageResponse.model_validate(all_images[idx]))
                matched_distances.append(float(dist))

        return SimilaritySearchResponse(
            query_image=file.filename,
            results=matched_images,
            distances=matched_distances,
        )

    finally:
        if tmp_path.exists():
            tmp_path.unlink()
