"""Abstract base class for embedding models."""

from abc import ABC, abstractmethod

import numpy as np
import torch


class BaseEmbeddingModel(ABC):
    """Base class for all self-supervised embedding models.

    All models must implement `extract_single` and `extract_batch`.
    """

    def __init__(self, device: str = "cpu"):
        self.device = torch.device(device)
        self.model: torch.nn.Module | None = None

    @abstractmethod
    def load_model(self) -> None:
        """Load the pretrained model."""
        ...

    @abstractmethod
    def extract_single(self, image_tensor: torch.Tensor) -> np.ndarray:
        """Extract embedding for a single image tensor.

        Args:
            image_tensor: Preprocessed image tensor [C, H, W].

        Returns:
            Embedding vector as numpy array [D].
        """
        ...

    @abstractmethod
    def extract_batch(
        self, image_tensors: torch.Tensor, batch_size: int = 32
    ) -> np.ndarray:
        """Extract embeddings for a batch of images.

        Args:
            image_tensors: Batch of image tensors [N, C, H, W].
            batch_size: Processing batch size.

        Returns:
            Embeddings as numpy array [N, D].
        """
        ...

    @property
    @abstractmethod
    def embedding_dim(self) -> int:
        """Dimensionality of the output embeddings."""
        ...

    def _ensure_loaded(self) -> None:
        """Ensure the model is loaded before inference."""
        if self.model is None:
            self.load_model()
