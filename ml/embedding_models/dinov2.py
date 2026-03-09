"""DINOv2 embedding model wrapper.

Uses Facebook's DINOv2 self-supervised vision transformer via torch.hub.
Supports ViT-S/14, ViT-B/14, and ViT-L/14 variants.
"""

import numpy as np
import torch
from loguru import logger

from ml.embedding_models.base import BaseEmbeddingModel

# DINOv2 variant → (hub_name, embedding_dim)
DINOV2_VARIANTS = {
    "vits14": ("dinov2_vits14", 384),
    "vitb14": ("dinov2_vitb14", 768),
    "vitl14": ("dinov2_vitl14", 1024),
}


class DINOv2Model(BaseEmbeddingModel):
    """DINOv2 self-supervised embedding model.

    DINOv2 learns visual features without labels using a student-teacher
    framework with vision transformers. It produces high-quality embeddings
    suitable for clustering, retrieval, and similarity search.
    """

    def __init__(self, variant: str = "vitb14", device: str = "cpu"):
        super().__init__(device)
        if variant not in DINOV2_VARIANTS:
            raise ValueError(f"Unknown DINOv2 variant: {variant}. Choose from {list(DINOV2_VARIANTS)}")
        self.variant = variant
        self._hub_name, self._dim = DINOV2_VARIANTS[variant]

    def load_model(self) -> None:
        """Load DINOv2 from torch.hub (downloads weights on first run)."""
        logger.info(f"Loading DINOv2 ({self.variant}) on {self.device}")
        self.model = torch.hub.load("facebookresearch/dinov2", self._hub_name)
        self.model = self.model.to(self.device)
        self.model.eval()
        logger.info(f"DINOv2 loaded — embedding dim: {self._dim}")

    @property
    def embedding_dim(self) -> int:
        return self._dim

    @torch.no_grad()
    def extract_single(self, image_tensor: torch.Tensor) -> np.ndarray:
        """Extract embedding for a single image.

        Args:
            image_tensor: Tensor of shape [C, H, W] or [1, C, H, W].

        Returns:
            Numpy array of shape [D].
        """
        self._ensure_loaded()
        if image_tensor.dim() == 3:
            image_tensor = image_tensor.unsqueeze(0)
        image_tensor = image_tensor.to(self.device)
        embedding = self.model(image_tensor)
        return embedding.cpu().numpy().flatten()

    @torch.no_grad()
    def extract_batch(
        self, image_tensors: torch.Tensor, batch_size: int = 32
    ) -> np.ndarray:
        """Extract embeddings for a batch of images.

        Args:
            image_tensors: Tensor of shape [N, C, H, W].
            batch_size: Number of images per forward pass.

        Returns:
            Numpy array of shape [N, D].
        """
        self._ensure_loaded()
        all_embeddings = []
        n = image_tensors.shape[0]

        for i in range(0, n, batch_size):
            batch = image_tensors[i : i + batch_size].to(self.device)
            embeddings = self.model(batch)
            all_embeddings.append(embeddings.cpu().numpy())
            logger.debug(f"DINOv2: processed batch {i // batch_size + 1}/{(n + batch_size - 1) // batch_size}")

        return np.vstack(all_embeddings)
