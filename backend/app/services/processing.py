"""Dataset processing pipeline orchestrator.

Coordinates: embedding generation → FAISS indexing → clustering →
duplicate detection → outlier detection → UMAP projection.
"""

import sys
from pathlib import Path

import numpy as np
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Add project root to path for ML imports
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.config import settings
from app.database import async_session
from app.models.dataset import Dataset
from app.models.image import Image
from app.models.schemas import ProcessingRequest


async def process_dataset_pipeline(
    dataset_id: str,
    request: ProcessingRequest,
) -> None:
    """Run the full ML processing pipeline for a dataset.

    Steps:
        1. Load images and compute embeddings
        2. Build FAISS index
        3. Run clustering
        4. Detect duplicates
        5. Detect outliers
        6. Compute UMAP projections
        7. Update database records
    """
    async with async_session() as db:
        try:
            await _update_status(db, dataset_id, "processing", "Loading images...")
            logger.info(f"[Pipeline] Starting processing for dataset {dataset_id}")

            # 1. Get image records
            result = await db.execute(
                select(Image)
                .where(Image.dataset_id == dataset_id)
                .order_by(Image.created_at)
            )
            images = list(result.scalars().all())

            if not images:
                await _update_status(db, dataset_id, "failed", "No images found")
                return

            image_paths = [img.filepath for img in images]
            logger.info(f"[Pipeline] Found {len(images)} images")

            # 2. Compute embeddings
            await _update_status(db, dataset_id, "processing", "Computing embeddings...")
            embeddings = await _compute_embeddings(image_paths, request.model_name)
            logger.info(f"[Pipeline] Embeddings shape: {embeddings.shape}")

            # Mark images as having embeddings
            for img in images:
                img.has_embedding = True
                img.embedding_model = request.model_name

            # 3. Build FAISS index
            await _update_status(db, dataset_id, "processing", "Building search index...")
            from ml.embeddings.faiss_index import FAISSIndex

            faiss_index = FAISSIndex(dim=embeddings.shape[1])
            faiss_index.build(embeddings)
            index_path = settings.FAISS_INDEX_DIR / f"{dataset_id}.index"
            faiss_index.save(str(index_path))
            logger.info("[Pipeline] FAISS index built and saved")

            # Save embeddings cache
            cache_path = settings.EMBEDDINGS_CACHE_DIR / f"{dataset_id}.npy"
            np.save(str(cache_path), embeddings)

            # 4. Clustering
            await _update_status(db, dataset_id, "processing", "Clustering images...")
            from ml.clustering.clustering import ClusterEngine

            cluster_engine = ClusterEngine(
                method=request.cluster_method,
                n_clusters=request.n_clusters,
            )
            cluster_labels = cluster_engine.fit_predict(embeddings)
            n_clusters = len(set(cluster_labels) - {-1})

            for img, label in zip(images, cluster_labels):
                img.cluster_id = int(label)

            logger.info(f"[Pipeline] Found {n_clusters} clusters")

            # 5. Duplicate detection
            duplicate_count = 0
            if request.detect_duplicates:
                await _update_status(db, dataset_id, "processing", "Detecting duplicates...")
                from ml.outlier_detection.duplicate_detection import DuplicateDetector

                dup_detector = DuplicateDetector(threshold=settings.DUPLICATE_THRESHOLD)
                dup_groups = dup_detector.detect(embeddings)

                for group_id, indices in dup_groups.items():
                    for idx in indices:
                        images[idx].is_duplicate = True
                        images[idx].duplicate_group_id = group_id
                        duplicate_count += 1

                logger.info(f"[Pipeline] Found {len(dup_groups)} duplicate groups ({duplicate_count} images)")

            # 6. Outlier detection
            outlier_count = 0
            if request.detect_outliers:
                await _update_status(db, dataset_id, "processing", "Detecting outliers...")
                from ml.outlier_detection.outlier_detection import OutlierDetector

                outlier_detector = OutlierDetector()
                outlier_scores, outlier_mask = outlier_detector.detect(embeddings)

                for img, score, is_outlier in zip(images, outlier_scores, outlier_mask):
                    img.outlier_score = float(score)
                    img.is_outlier = bool(is_outlier)
                    if is_outlier:
                        outlier_count += 1

                logger.info(f"[Pipeline] Found {outlier_count} outliers")

            # 7. UMAP projection
            if request.generate_map:
                await _update_status(db, dataset_id, "processing", "Generating embedding map...")
                from ml.embeddings.dimensionality_reduction import DimensionalityReducer

                reducer = DimensionalityReducer(
                    n_components=3,
                    n_neighbors=min(settings.UMAP_N_NEIGHBORS, len(images) - 1),
                    min_dist=settings.UMAP_MIN_DIST,
                )
                coords = reducer.fit_transform(embeddings)

                for img, coord in zip(images, coords):
                    img.umap_x = float(coord[0])
                    img.umap_y = float(coord[1])
                    img.umap_z = float(coord[2]) if len(coord) > 2 else 0.0

                logger.info("[Pipeline] UMAP projection computed")

            # 8. Update dataset summary
            ds_result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
            dataset = ds_result.scalar_one()
            dataset.status = "completed"
            dataset.processed_count = len(images)
            dataset.cluster_count = n_clusters
            dataset.duplicate_count = duplicate_count
            dataset.outlier_count = outlier_count
            dataset.duplicate_percentage = (
                (duplicate_count / len(images) * 100) if images else 0.0
            )
            dataset.embedding_dim = embeddings.shape[1]
            dataset.stats = {
                "embedding_shape": list(embeddings.shape),
                "n_clusters": n_clusters,
                "n_duplicates": duplicate_count,
                "n_outliers": outlier_count,
                "model": request.model_name,
                "cluster_method": request.cluster_method,
            }

            await db.commit()
            logger.info(f"[Pipeline] Dataset {dataset_id} processing complete!")

        except Exception as e:
            logger.error(f"[Pipeline] Processing failed: {e}")
            await _update_status(db, dataset_id, "failed", str(e))
            await db.commit()
            raise


async def _update_status(db: AsyncSession, dataset_id: str, status: str, message: str) -> None:
    """Update dataset processing status."""
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if dataset:
        dataset.status = status
        await db.flush()
    logger.info(f"[Pipeline] Status: {message}")


async def _compute_embeddings(image_paths: list[str], model_name: str) -> np.ndarray:
    """Compute embeddings for a list of image paths."""
    from ml.preprocessing.preprocessing import preprocess_batch

    # Preprocess images
    tensors = preprocess_batch(image_paths, settings.IMAGE_SIZE)

    # Load model and extract
    if model_name == "dinov2":
        from ml.embedding_models.dinov2 import DINOv2Model
        model = DINOv2Model(variant=settings.DINOV2_VARIANT, device=settings.DEVICE)
    elif model_name == "simclr":
        from ml.embedding_models.simclr import SimCLRModel
        model = SimCLRModel(device=settings.DEVICE)
    elif model_name == "moco":
        from ml.embedding_models.moco import MoCoModel
        model = MoCoModel(device=settings.DEVICE)
    else:
        from ml.embedding_models.dinov2 import DINOv2Model
        model = DINOv2Model(variant=settings.DINOV2_VARIANT, device=settings.DEVICE)

    embeddings = model.extract_batch(tensors, batch_size=settings.BATCH_SIZE)
    return embeddings
