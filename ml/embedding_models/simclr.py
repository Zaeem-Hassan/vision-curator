"""SimCLR embedding model wrapper.

SimCLR (Simple Framework for Contrastive Learning of Visual Representations)
uses a ResNet50 backbone with contrastive learning objective.
"""

import numpy as np
import torch
import torch.nn as nn
from loguru import logger
from torchvision import models

from ml.embedding_models.base import BaseEmbeddingModel


class SimCLRModel(BaseEmbeddingModel):
    """SimCLR self-supervised model with ResNet50 backbone.

    We use a torchvision ResNet50 (pretrained on ImageNet) as a practical
    stand-in. For a fully self-supervised variant, you would fine-tune
    with the NT-Xent contrastive loss on your dataset.
    """

    def __init__(self, device: str = "cpu"):
        super().__init__(device)
        self._dim = 2048  # ResNet50 final pooling dim

    def load_model(self) -> None:
        """Load ResNet50 backbone (removing the classification head)."""
        logger.info(f"Loading SimCLR (ResNet50) on {self.device}")
        backbone = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
        # Remove final FC layer — use avgpool output as embedding
        self.model = nn.Sequential(*list(backbone.children())[:-1])
        self.model = self.model.to(self.device)
        self.model.eval()
        logger.info(f"SimCLR loaded — embedding dim: {self._dim}")

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
            all_embeddings.append(embeddings.view(batch.size(0), -1).cpu().numpy())
            logger.debug(f"SimCLR: batch {i // batch_size + 1}/{(n + batch_size - 1) // batch_size}")

        return np.vstack(all_embeddings)
