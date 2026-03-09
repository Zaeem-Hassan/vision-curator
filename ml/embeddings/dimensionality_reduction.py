"""Dimensionality reduction for embedding visualization.

Supports UMAP and t-SNE for projecting high-dimensional embeddings
into 2D or 3D for interactive visualization.
"""

import numpy as np
from loguru import logger


class DimensionalityReducer:
    """UMAP / t-SNE dimensionality reducer.

    Primary: UMAP (better at preserving global structure).
    Fallback: t-SNE (sklearn, slower but always available).
    """

    def __init__(
        self,
        method: str = "umap",
        n_components: int = 3,
        n_neighbors: int = 15,
        min_dist: float = 0.1,
        random_state: int = 42,
    ):
        self.method = method
        self.n_components = n_components
        self.n_neighbors = n_neighbors
        self.min_dist = min_dist
        self.random_state = random_state

    def fit_transform(self, embeddings: np.ndarray) -> np.ndarray:
        """Project embeddings to lower dimensions.

        Args:
            embeddings: Array of shape [N, D].

        Returns:
            Array of shape [N, n_components].
        """
        n_samples = embeddings.shape[0]
        logger.info(
            f"Reducing {embeddings.shape} to {self.n_components}D via {self.method}"
        )

        # Adjust n_neighbors for small datasets
        effective_neighbors = min(self.n_neighbors, max(2, n_samples - 1))

        if self.method == "umap":
            return self._umap_reduce(embeddings, effective_neighbors)
        elif self.method == "tsne":
            return self._tsne_reduce(embeddings)
        else:
            logger.warning(f"Unknown method '{self.method}', falling back to UMAP")
            return self._umap_reduce(embeddings, effective_neighbors)

    def _umap_reduce(self, embeddings: np.ndarray, n_neighbors: int) -> np.ndarray:
        """UMAP projection."""
        try:
            import umap

            reducer = umap.UMAP(
                n_components=self.n_components,
                n_neighbors=n_neighbors,
                min_dist=self.min_dist,
                random_state=self.random_state,
                metric="cosine",
            )
            result = reducer.fit_transform(embeddings)
            logger.info(f"UMAP complete: {result.shape}")
            return result
        except ImportError:
            logger.warning("umap-learn not installed, falling back to t-SNE")
            return self._tsne_reduce(embeddings)

    def _tsne_reduce(self, embeddings: np.ndarray) -> np.ndarray:
        """t-SNE projection."""
        from sklearn.manifold import TSNE

        n_components = min(self.n_components, 3)  # t-SNE max 3D
        perplexity = min(30.0, max(5.0, embeddings.shape[0] / 4.0))

        tsne = TSNE(
            n_components=n_components,
            perplexity=perplexity,
            random_state=self.random_state,
            metric="cosine",
        )
        result = tsne.fit_transform(embeddings)
        logger.info(f"t-SNE complete: {result.shape}")
        return result
