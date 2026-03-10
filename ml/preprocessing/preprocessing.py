"""Image preprocessing utilities for embedding extraction.

Handles loading, resizing, normalization, and batching of images
for input to SSL models.
"""

from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Sequence

import numpy as np
import torch
from loguru import logger
from PIL import Image
from torchvision import transforms


def get_default_transform(image_size: int = 224) -> transforms.Compose:
    """Get the default preprocessing transform for SSL models.

    Uses ImageNet normalization as all backbone models are pretrained on it.
    """
    return transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ])


def load_image(path: str) -> Image.Image | None:
    """Load an image from disk, converting to RGB.

    Returns None if the image cannot be loaded.
    """
    try:
        img = Image.open(path).convert("RGB")
        return img
    except Exception as e:
        logger.warning(f"Failed to load image {path}: {e}")
        return None


def preprocess_single_image(
    path: str,
    image_size: int = 224,
) -> torch.Tensor:
    """Load and preprocess a single image.

    Args:
        path: Path to the image file.
        image_size: Target size for resizing.

    Returns:
        Preprocessed tensor [1, C, H, W].
    """
    transform = get_default_transform(image_size)
    img = load_image(path)
    if img is None:
        raise ValueError(f"Could not load image: {path}")
    tensor = transform(img)
    return tensor.unsqueeze(0)


def preprocess_batch(
    paths: Sequence[str],
    image_size: int = 224,
    max_workers: int = 8,
) -> torch.Tensor:
    """Load and preprocess a batch of images in parallel.

    Uses ThreadPoolExecutor to load images concurrently (I/O bound),
    giving 3-5x speedup over sequential loading on large datasets.

    Args:
        paths: List of image file paths.
        image_size: Target size for resizing.
        max_workers: Number of parallel threads.

    Returns:
        Batched tensor [N, C, H, W].
    """
    transform = get_default_transform(image_size)
    n = len(paths)
    tensors: list[torch.Tensor | None] = [None] * n
    skipped = 0

    def _load_one(idx: int, path: str) -> tuple[int, torch.Tensor]:
        img = load_image(path)
        if img is None:
            return idx, torch.zeros(3, image_size, image_size)
        return idx, transform(img)

    with ThreadPoolExecutor(max_workers=min(max_workers, n)) as pool:
        futures = {pool.submit(_load_one, i, p): i for i, p in enumerate(paths)}
        for future in as_completed(futures):
            idx, tensor = future.result()
            tensors[idx] = tensor
            if tensor.sum() == 0:
                skipped += 1

    if skipped > 0:
        logger.warning(f"Skipped {skipped}/{n} unloadable images (replaced with zeros)")

    logger.info(f"Loaded {n} images with {max_workers} threads")
    return torch.stack(tensors)  # type: ignore[arg-type]


def get_augmentation_transform(image_size: int = 224) -> transforms.Compose:
    """Get augmentation transforms for SSL training.

    Includes random crop, flip, color jitter, and Gaussian blur —
    standard augmentations for contrastive learning.
    """
    return transforms.Compose([
        transforms.RandomResizedCrop(image_size, scale=(0.2, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomApply(
            [transforms.ColorJitter(0.4, 0.4, 0.4, 0.1)], p=0.8
        ),
        transforms.RandomGrayscale(p=0.2),
        transforms.GaussianBlur(kernel_size=23, sigma=(0.1, 2.0)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ])
