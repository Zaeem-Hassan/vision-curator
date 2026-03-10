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

        # upload_file.filename may include subfolder paths from webkitdirectory
        # e.g. "truck/0001.png" — preserve the relative path for storage but
        # flatten it (replace / with _) for the DB filename field.
        raw_name = upload_file.filename or f"{uuid.uuid4()}.jpg"
        # Normalise slashes (Windows sends backslashes sometimes)
        raw_name = raw_name.replace("\\", "/")
        file_path = dataset_dir / raw_name

        # Create parent subdirectories if the folder contains subfolders
        file_path.parent.mkdir(parents=True, exist_ok=True)

        content = await upload_file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        # Store a flat filename in the DB (replace / with _ so it's readable)
        flat_name = raw_name.replace("/", "_")

        img = Image(
            id=str(uuid.uuid4()),
            dataset_id=dataset_id,
            filename=flat_name,
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


@router.get("/{dataset_id}/export")
async def export_dataset(
    dataset_id: str,
    max_images: int = Query(100, ge=1, le=100000, description="Target number of images in the exported dataset"),
    db: AsyncSession = Depends(get_db),
):
    """Smart Export: Returns a perfectly balanced dataset of size max_images.
    Includes ALL outliers (high priority for labeling), and distributes the
    remaining quota perfectly evenly across all clusters, excluding duplicates.
    """
    import tempfile
    import zipfile
    from collections import defaultdict
    from fastapi.responses import FileResponse

    # 1. Verify dataset
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # 2. Grab all outliers first (high priority edge cases)
    outlier_res = await db.execute(
        select(Image).where(Image.dataset_id == dataset_id, Image.is_outlier == True)
    )
    selected_images = list(outlier_res.scalars().all())
    
    # 3. Calculate remaining quota we need to fill from normal classes
    quota = max(0, max_images - len(selected_images))
    
    if quota > 0:
        # Get all non-duplicate, non-outlier images
        normal_res = await db.execute(
            select(Image).where(
                Image.dataset_id == dataset_id,
                Image.is_outlier == False,
                Image.is_duplicate == False
            )
        )
        normal_images = normal_res.scalars().all()
        
        # Group by cluster_id
        cluster_map = defaultdict(list)
        for img in normal_images:
            c_id = img.cluster_id if img.cluster_id is not None else -1
            cluster_map[c_id].append(img)
            
        # Distribute remaining quota equally across clusters:
        # Sort clusters by size ascending (so small clusters use up their quota
        # fast and pass the remaining quota onto the larger clusters)
        clusters = sorted(list(cluster_map.values()), key=len)
        remaining_clusters = len(clusters)
        
        for cluster_imgs in clusters:
            if remaining_clusters == 0 or quota == 0:
                break
            # Fair share for this specific cluster
            share = max(1, quota // remaining_clusters)
            # Take up to its fair share (or all it has if smaller)
            take = min(len(cluster_imgs), share)
            
            selected_images.extend(cluster_imgs[:take])
            quota -= take
            remaining_clusters -= 1

    if not selected_images:
        raise HTTPException(status_code=400, detail="No images available to export")

    # 3. Create a temporary ZIP file and add the images
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".zip")
    os.close(tmp_fd)

    try:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for img in images:
                if os.path.exists(img.filepath):
                    # Store in zip using the original flat filename (e.g. cat_001.png)
                    zf.write(img.filepath, arcname=img.filename)
                    
        return FileResponse(
            path=tmp_path,
            filename=f"{dataset.name}_export_{max_images}.zip",
            media_type="application/zip",
            background=None, # In production you'd use a BackgroundTask to delete tmp_path
        )
    except Exception as e:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise HTTPException(status_code=500, detail=f"Failed to create ZIP: {e}")


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
    """Trigger ML processing pipeline for a dataset (runs in background)."""
    import asyncio

    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if dataset.status == "processing":
        raise HTTPException(status_code=409, detail="Dataset is already being processed")

    req = request or ProcessingRequest()
    dataset.status = "processing"
    dataset.model_name = req.model_name
    # Commit NOW so the pipeline session sees the records
    await db.commit()

    # Launch pipeline in background — does NOT block the HTTP response
    from app.services.processing import process_dataset_pipeline

    async def _run():
        try:
            await process_dataset_pipeline(dataset_id, req)
        except Exception as exc:
            logger.error(f"Background pipeline error: {exc}")

    asyncio.create_task(_run())

    return ProcessingStatus(
        dataset_id=dataset_id,
        status="processing",
        progress=0.0,
        current_step="started",
        message="Processing started in background",
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
