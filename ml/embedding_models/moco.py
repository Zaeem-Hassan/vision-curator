"""MoCo v3 embedding model wrapper.

MoCo (Momentum Contrast) is a self-supervised method using a momentum-updated
encoder. This wrapper uses a ViT-B backbone via torchvision.
"""

import numpy as np
import torch
import torch.nn as nn
from loguru import logger
from torchvision import models

from ml.embedding_models.base import BaseEmbeddingModel


class MoCoModel(BaseEmbeddingModel):
    """MoCo (Momentum Contrast) model with ViT backbone.

    Uses torchvision's ViT-B/16 as a practical backbone.
    For true MoCo v3, you would use the self-supervised pretrained weights
    from the official MoCo-v3 repository.
    """

    def __init__(self, device: str = "cpu"):
        super().__init__(device)
        self._dim = 768  # ViT-B hidden dim

    def load_model(self) -> None:
        """Load ViT-B/16 backbone."""
        logger.info(f"Loading MoCo (ViT-B/16) on {self.device}")
        vit = models.vit_b_16(weights=models.ViT_B_16_Weights.DEFAULT)
        # Remove classification head
        vit.heads = nn.Identity()
        self.model = vit.to(self.device)
        self.model.eval()
        logger.info(f"MoCo loaded — embedding dim: {self._dim}")

    @property
    def embedding_dim(self) -> int:
        return self._dim

    @torch.no_grad()
    def extract_single(self, image_tensor: torch.Tensor) -> np.ndarray:
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
        self._ensure_loaded()
        all_embeddings = []
        n = image_tensors.shape[0]

        for i in range(0, n, batch_size):
            batch = image_tensors[i : i + batch_size].to(self.device)
            embeddings = self.model(batch)
            all_embeddings.append(embeddings.cpu().numpy())
            logger.debug(f"MoCo: batch {i // batch_size + 1}/{(n + batch_size - 1) // batch_size}")

        return np.vstack(all_embeddings)
