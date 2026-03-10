"""Dataset processing pipeline orchestrator.

Runs entirely synchronously inside asyncio.to_thread() so it never
blocks the FastAPI event loop. Uses synchronous SQLAlchemy (SyncSession)
to avoid nested event-loop problems on Windows with aiosqlite.

Pipeline steps:
  1. Load image records from DB
  2. Compute embeddings (PyTorch model)
  3. PCA whitening
  4. Build FAISS index
  5. Cluster images
  6. Detect duplicates
  7. Detect outliers
  8. UMAP 3-D projection
  9. Write results back to DB
"""

import sys
import traceback
from pathlib import Path

import numpy as np
from loguru import logger

# Ensure ml/ package is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.config import settings
from app.models.schemas import ProcessingRequest


# ── Public entry-point called by the API endpoint ────────────────────────────


async def process_dataset_pipeline(dataset_id: str, request: ProcessingRequest) -> None:
    """Run the full ML pipeline in a background thread (non-blocking)."""
    import asyncio
    await asyncio.to_thread(_run_sync, dataset_id, request)


# ── Synchronous pipeline  ─────────────────────────────────────────────────────


def _run_sync(dataset_id: str, request: ProcessingRequest) -> None:
    """The full pipeline — pure synchronous, runs in a thread-pool worker."""
    from app.database import SyncSession
    from app.models.dataset import Dataset
    from app.models.image import Image

    db = SyncSession()
    try:
        logger.info(f"[Pipeline] ▶ Starting dataset {dataset_id}")
        _set_status(db, dataset_id, "processing")

        # ── 1. Fetch image records ────────────────────────────────────────────
        images = db.query(Image).filter(Image.dataset_id == dataset_id).order_by(Image.created_at).all()

        if not images:
            logger.error("[Pipeline] No images found — aborting")
            _set_status(db, dataset_id, "failed")
            db.commit()
            return

        image_paths = [img.filepath for img in images]
        n = len(images)
        logger.info(f"[Pipeline] {n} images found")

        # ── 2. Compute embeddings ─────────────────────────────────────────────
        logger.info(f"[Pipeline] Computing embeddings with model={request.model_name}")
        embeddings = _compute_embeddings(image_paths, request.model_name)
        logger.info(f"[Pipeline] Raw embeddings: {embeddings.shape}")

        for img in images:
            img.has_embedding = True
            img.embedding_model = request.model_name

        # ── 3. FAISS index ────────────────────────────────────────────────────
        logger.info("[Pipeline] Building FAISS index")
        from ml.embeddings.faiss_index import FAISSIndex
        idx = FAISSIndex(dim=embeddings.shape[1])
        idx.build(embeddings)
        settings.FAISS_INDEX_DIR.mkdir(parents=True, exist_ok=True)
        idx.save(str(settings.FAISS_INDEX_DIR / f"{dataset_id}.index"))

        settings.EMBEDDINGS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        np.save(str(settings.EMBEDDINGS_CACHE_DIR / f"{dataset_id}.npy"), embeddings)

        # ── 5. Clustering ─────────────────────────────────────────────────────
        logger.info("[Pipeline] Clustering")
        from ml.clustering.clustering import ClusterEngine
        ce = ClusterEngine(
            method=request.cluster_method,
            n_clusters=request.n_clusters,
            reduce_before_cluster=(n >= 10),
        )
        labels = ce.fit_predict(embeddings)
        n_clusters = len(set(labels.tolist()) - {-1})

        for img, lbl in zip(images, labels.tolist()):
            img.cluster_id = int(lbl)
        logger.info(f"[Pipeline] {n_clusters} clusters")

        # ── 6. Duplicate detection ────────────────────────────────────────────
        duplicate_count = 0
        if request.detect_duplicates and n >= 2:
            logger.info("[Pipeline] Detecting duplicates")
            from ml.outlier_detection.duplicate_detection import DuplicateDetector
            dd = DuplicateDetector(threshold=settings.DUPLICATE_THRESHOLD)
            groups = dd.detect(embeddings)
            for group_id, indices in groups.items():
                for idx_i in indices:
                    if 0 <= idx_i < n:
                        images[idx_i].is_duplicate = True
                        images[idx_i].duplicate_group_id = group_id
                        duplicate_count += 1
            logger.info(f"[Pipeline] {len(groups)} dup groups, {duplicate_count} images")

        # ── 7. Outlier detection ──────────────────────────────────────────────
        outlier_count = 0
        if request.detect_outliers and n >= 5:
            logger.info("[Pipeline] Detecting outliers")
            from ml.outlier_detection.outlier_detection import OutlierDetector
            od = OutlierDetector(
                contamination=min(settings.OUTLIER_CONTAMINATION, 0.45),
                n_neighbors=min(settings.OUTLIER_KNN_NEIGHBORS, n - 1),
            )
            scores, mask = od.detect(embeddings)
            for img, score, is_out in zip(images, scores.tolist(), mask.tolist()):
                img.outlier_score = float(score)
                img.is_outlier = bool(is_out)
                if is_out:
                    outlier_count += 1
            logger.info(f"[Pipeline] {outlier_count} outliers")

        # ── 8. UMAP projection ────────────────────────────────────────────────
        if request.generate_map and n >= 3:
            logger.info("[Pipeline] Computing UMAP 3-D projection")
            from ml.embeddings.dimensionality_reduction import DimensionalityReducer
            reducer = DimensionalityReducer(
                n_components=3,
                n_neighbors=min(settings.UMAP_N_NEIGHBORS, n - 1),
                min_dist=settings.UMAP_MIN_DIST,
            )
            coords = reducer.fit_transform(embeddings)
            for img, coord in zip(images, coords):
                img.umap_x = float(coord[0])
                img.umap_y = float(coord[1])
                img.umap_z = float(coord[2]) if coord.shape[0] > 2 else 0.0
            logger.info("[Pipeline] UMAP done")

        # ── 9. Update dataset record ──────────────────────────────────────────
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if dataset:
            dataset.status = "completed"
            dataset.processed_count = n
            dataset.cluster_count = n_clusters
            dataset.duplicate_count = duplicate_count
            dataset.outlier_count = outlier_count
            dataset.duplicate_percentage = duplicate_count / n * 100 if n else 0.0
            dataset.embedding_dim = int(embeddings.shape[1])
            dataset.stats = {
                "embedding_shape": list(embeddings.shape),
                "n_clusters": n_clusters,
                "n_duplicates": duplicate_count,
                "n_outliers": outlier_count,
                "model": request.model_name,
                "cluster_method": request.cluster_method,
            }

        db.commit()
        logger.info(f"[Pipeline] ✓ Dataset {dataset_id} completed")

    except Exception as exc:
        logger.error(f"[Pipeline] ✗ Failed: {exc}")
        logger.error(traceback.format_exc())
        try:
            _set_status(db, dataset_id, "failed")
            db.commit()
        except Exception:
            db.rollback()
    finally:
        db.close()


# ── Helpers ───────────────────────────────────────────────────────────────────


def _set_status(db, dataset_id: str, status: str) -> None:
    from app.models.dataset import Dataset
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if ds:
        ds.status = status
        db.flush()


def _compute_embeddings(image_paths: list[str], model_name: str) -> np.ndarray:
    """Preprocess images and extract embeddings from the chosen model."""
    from ml.preprocessing.preprocessing import preprocess_batch
    tensors = preprocess_batch(image_paths, settings.IMAGE_SIZE)

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
        # Default: ResNet50 from torchvision — no extra download needed
        from ml.embedding_models.resnet import ResNetModel
        model = ResNetModel(device=settings.DEVICE)

    return model.extract_batch(tensors, batch_size=settings.BATCH_SIZE)


def _whiten(embeddings: np.ndarray, n_components: int) -> np.ndarray:
    """PCA whitening: decorrelate dimensions and equalise variance."""
    n, d = embeddings.shape
    k = max(2, min(n_components, d, n - 1))
    if n < 3 or k <= 0:
        return embeddings
    try:
        from sklearn.decomposition import PCA
        pca = PCA(n_components=k, whiten=True, random_state=42)
        out = np.ascontiguousarray(pca.fit_transform(embeddings), dtype=np.float32)
        explained = pca.explained_variance_ratio_.sum() * 100
        logger.info(f"[Whiten] {d}D → {k}D  ({explained:.1f}% variance retained)")
        return out
    except Exception as e:
        logger.warning(f"[Whiten] PCA skipped: {e}")
        return embeddings
