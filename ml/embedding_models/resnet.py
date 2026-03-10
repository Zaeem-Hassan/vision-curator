"""Fast ResNet50 embedding model using torchvision pretrained weights.

Uses ResNet50 pretrained on ImageNet (bundled with torchvision — no extra
download needed). Embeddings come from the penultimate layer (2048-D).

This is the default model used when DINOv2 is not available or too slow.
"""

import numpy as np
import torch
import torch.nn as nn
from loguru import logger
from torchvision import models

from ml.embedding_models.base import BaseEmbeddingModel


class ResNetModel(BaseEmbeddingModel):
    """ResNet50 embedding extractor using torchvision pretrained weights.

    Removes the final classification head and uses global average pooling
    output as the 2048-D embedding vector.
    """

    def __init__(self, device: str = "cpu"):
        super().__init__(device)
        self._dim = 2048

    @property
    def embedding_dim(self) -> int:
        return self._dim

    def load_model(self) -> None:
        """Load ResNet50 pretrained on ImageNet (from torchvision cache)."""
        logger.info(f"Loading ResNet50 pretrained on {self.device}")
        backbone = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)
        # Remove the classification head — keep everything up to avgpool
        self.model = nn.Sequential(*list(backbone.children())[:-1])
        self.model = self.model.to(self.device)
        self.model.eval()
        logger.info("ResNet50 loaded — embedding dim: 2048")

    @torch.inference_mode()
    def extract_single(self, image_tensor: torch.Tensor) -> np.ndarray:
        self._ensure_loaded()
        if image_tensor.dim() == 3:
            image_tensor = image_tensor.unsqueeze(0)
        image_tensor = image_tensor.to(self.device)
        embedding = self.model(image_tensor)
        return embedding.squeeze().cpu().numpy()

    @torch.inference_mode()
    def extract_batch(self, image_tensors: torch.Tensor, batch_size: int = 64) -> np.ndarray:
        self._ensure_loaded()
        all_embeddings = []
        n = image_tensors.shape[0]

        for i in range(0, n, batch_size):
            batch = image_tensors[i: i + batch_size].to(self.device)
            embeddings = self.model(batch)
            # Shape: [B, 2048, 1, 1] → [B, 2048]
            embeddings = embeddings.squeeze(-1).squeeze(-1)
            all_embeddings.append(embeddings.cpu().numpy())
            logger.debug(f"ResNet50: batch {i // batch_size + 1}/{(n + batch_size - 1) // batch_size}")

        return np.vstack(all_embeddings)
