"""Celery tasks for background processing."""

import asyncio

from loguru import logger

from app.models.schemas import ProcessingRequest
from app.services.celery_app import celery_app


@celery_app.task(bind=True, name="process_dataset")
def process_dataset_task(self, dataset_id: str, config: dict | None = None) -> dict:
    """Celery task to process a dataset asynchronously.

    Args:
        dataset_id: The dataset ID to process.
        config: Optional processing configuration dict.

    Returns:
        dict with status and results.
    """
    logger.info(f"[Celery] Starting task for dataset {dataset_id}")

    request = ProcessingRequest(**(config or {}))

    from app.services.processing import process_dataset_pipeline

    # Run async pipeline in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(process_dataset_pipeline(dataset_id, request))
        return {"status": "completed", "dataset_id": dataset_id}
    except Exception as e:
        logger.error(f"[Celery] Task failed: {e}")
        return {"status": "failed", "dataset_id": dataset_id, "error": str(e)}
    finally:
        loop.close()
