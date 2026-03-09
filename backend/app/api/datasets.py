"""Dataset API endpoints."""

import os
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.dataset import Dataset
from app.models.image import Image
from app.models.schemas import (
    ClusterInfo,
    ClusterListResponse,
    DatasetCreate,
    DatasetListResponse,
    DatasetResponse,
    DuplicateGroup,
    DuplicateListResponse,
    ImageListResponse,
    ImageResponse,
    OutlierListResponse,
    ProcessingRequest,
    ProcessingStatus,
)

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("/upload", response_model=DatasetResponse, status_code=201)
async def upload_dataset(
    name: str,
    description: str = "",
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
) -> DatasetResponse:
    """Upload a new image dataset with files."""
    dataset_id = str(uuid.uuid4())
    dataset_dir = settings.UPLOAD_DIR / dataset_id
    dataset_dir.mkdir(parents=True, exist_ok=True)

    # Create dataset record
    dataset = Dataset(
        id=dataset_id,
        name=name,
        description=description or None,
        image_count=len(files),
        status="pending",
    )
    db.add(dataset)

    # Save files and create image records
    image_records = []
    for upload_file in files:
        if not upload_file.content_type or not upload_file.content_type.startswith("image/"):
            continue

        filename = upload_file.filename or f"{uuid.uuid4()}.jpg"
        file_path = dataset_dir / filename

        content = await upload_file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        img = Image(
            id=str(uuid.uuid4()),
            dataset_id=dataset_id,
            filename=filename,
            filepath=str(file_path),
            file_size=len(content),
        )
        image_records.append(img)
        db.add(img)

    dataset.image_count = len(image_records)
    await db.flush()
    await db.refresh(dataset)

    logger.info(f"Dataset '{name}' uploaded with {len(image_records)} images")
    return DatasetResponse.model_validate(dataset)


@router.get("", response_model=DatasetListResponse)
async def list_datasets(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> DatasetListResponse:
    """List all datasets with pagination."""
    total_q = await db.execute(select(func.count(Dataset.id)))
    total = total_q.scalar() or 0

    result = await db.execute(
        select(Dataset).order_by(Dataset.created_at.desc()).offset(skip).limit(limit)
    )
    datasets = result.scalars().all()

    return DatasetListResponse(
        datasets=[DatasetResponse.model_validate(d) for d in datasets],
        total=total,
    )


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
) -> DatasetResponse:
    """Get dataset details by ID."""
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return DatasetResponse.model_validate(dataset)


@router.delete("/{dataset_id}", status_code=204)
async def delete_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a dataset and all associated data."""
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Remove files
    dataset_dir = settings.UPLOAD_DIR / dataset_id
    if dataset_dir.exists():
        shutil.rmtree(dataset_dir)

    # Remove FAISS index
    index_path = settings.FAISS_INDEX_DIR / f"{dataset_id}.index"
    if index_path.exists():
        index_path.unlink()

    await db.delete(dataset)
    logger.info(f"Dataset '{dataset.name}' deleted")


@router.post("/{dataset_id}/process", response_model=ProcessingStatus)
async def process_dataset(
    dataset_id: str,
    request: ProcessingRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> ProcessingStatus:
    """Trigger ML processing pipeline for a dataset."""
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if dataset.status == "processing":
        raise HTTPException(status_code=409, detail="Dataset is already being processed")

    req = request or ProcessingRequest()
    dataset.status = "processing"
    dataset.model_name = req.model_name
    await db.flush()

    # Trigger async processing (inline for now, Celery integration later)
    from app.services.processing import process_dataset_pipeline

    try:
        await process_dataset_pipeline(dataset_id, req)
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        dataset.status = "failed"
        await db.flush()

    return ProcessingStatus(
        dataset_id=dataset_id,
        status=dataset.status,
        progress=0.0,
        current_step="queued",
        message="Processing started",
    )


@router.get("/{dataset_id}/images", response_model=ImageListResponse)
async def get_dataset_images(
    dataset_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> ImageListResponse:
    """Get images for a dataset with pagination."""
    total_q = await db.execute(
        select(func.count(Image.id)).where(Image.dataset_id == dataset_id)
    )
    total = total_q.scalar() or 0

    result = await db.execute(
        select(Image)
        .where(Image.dataset_id == dataset_id)
        .order_by(Image.created_at)
        .offset(skip)
        .limit(limit)
    )
    images = result.scalars().all()

    return ImageListResponse(
        images=[ImageResponse.model_validate(i) for i in images],
        total=total,
    )


@router.get("/{dataset_id}/clusters", response_model=ClusterListResponse)
async def get_dataset_clusters(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
) -> ClusterListResponse:
    """Get cluster info for a dataset."""
    # Get distinct cluster IDs
    cluster_q = await db.execute(
        select(Image.cluster_id, func.count(Image.id).label("size"))
        .where(Image.dataset_id == dataset_id, Image.cluster_id.isnot(None))
        .group_by(Image.cluster_id)
        .order_by(Image.cluster_id)
    )
    clusters_raw = cluster_q.all()

    clusters = []
    for cluster_id, size in clusters_raw:
        # Get sample images
        sample_q = await db.execute(
            select(Image)
            .where(Image.dataset_id == dataset_id, Image.cluster_id == cluster_id)
            .limit(6)
        )
        samples = sample_q.scalars().all()

        # Compute centroid from UMAP coords
        coord_q = await db.execute(
            select(
                func.avg(Image.umap_x),
                func.avg(Image.umap_y),
                func.avg(Image.umap_z),
            ).where(Image.dataset_id == dataset_id, Image.cluster_id == cluster_id)
        )
        cx, cy, cz = coord_q.one()

        clusters.append(
            ClusterInfo(
                cluster_id=cluster_id,
                size=size,
                centroid_x=cx,
                centroid_y=cy,
                centroid_z=cz,
                sample_images=[ImageResponse.model_validate(s) for s in samples],
            )
        )

    return ClusterListResponse(clusters=clusters, total=len(clusters))


@router.get("/{dataset_id}/duplicates", response_model=DuplicateListResponse)
async def get_dataset_duplicates(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
) -> DuplicateListResponse:
    """Get duplicate groups for a dataset."""
    group_q = await db.execute(
        select(Image.duplicate_group_id)
        .where(
            Image.dataset_id == dataset_id,
            Image.is_duplicate == True,
            Image.duplicate_group_id.isnot(None),
        )
        .distinct()
    )
    group_ids = [row[0] for row in group_q.all()]

    groups = []
    for gid in group_ids:
        img_q = await db.execute(
            select(Image).where(
                Image.dataset_id == dataset_id, Image.duplicate_group_id == gid
            )
        )
        imgs = img_q.scalars().all()
        groups.append(
            DuplicateGroup(
                group_id=gid,
                images=[ImageResponse.model_validate(i) for i in imgs],
            )
        )

    total_dups_q = await db.execute(
        select(func.count(Image.id)).where(
            Image.dataset_id == dataset_id, Image.is_duplicate == True
        )
    )
    total_dups = total_dups_q.scalar() or 0

    return DuplicateListResponse(
        groups=groups, total_groups=len(groups), total_duplicates=total_dups
    )


@router.get("/{dataset_id}/outliers", response_model=OutlierListResponse)
async def get_dataset_outliers(
    dataset_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> OutlierListResponse:
    """Get outlier images for a dataset."""
    total_q = await db.execute(
        select(func.count(Image.id)).where(
            Image.dataset_id == dataset_id, Image.is_outlier == True
        )
    )
    total = total_q.scalar() or 0

    result = await db.execute(
        select(Image)
        .where(Image.dataset_id == dataset_id, Image.is_outlier == True)
        .order_by(Image.outlier_score.desc())
        .offset(skip)
        .limit(limit)
    )
    outliers = result.scalars().all()

    return OutlierListResponse(
        outliers=[ImageResponse.model_validate(o) for o in outliers],
        total=total,
    )
