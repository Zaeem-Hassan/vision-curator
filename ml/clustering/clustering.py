"""Clustering engine for image embeddings.

Supports KMeans and HDBSCAN for semantic grouping of images
based on their embedding representations.
"""

import numpy as np
from loguru import logger
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


class ClusterEngine:
    """Image embedding clustering with KMeans or HDBSCAN.

    Attributes:
        method: Clustering algorithm ('kmeans' or 'hdbscan').
        n_clusters: Number of clusters for KMeans.
        min_cluster_size: Minimum cluster size for HDBSCAN.
    """

    def __init__(
        self,
        method: str = "kmeans",
        n_clusters: int = 10,
        min_cluster_size: int = 15,
        random_state: int = 42,
    ):
        self.method = method
        self.n_clusters = n_clusters
        self.min_cluster_size = min_cluster_size
        self.random_state = random_state
        self._model = None
        self._labels: np.ndarray | None = None

    def fit_predict(self, embeddings: np.ndarray) -> np.ndarray:
        """Cluster embeddings and return labels.

        Args:
            embeddings: Array of shape [N, D].

        Returns:
            Cluster labels array of shape [N].
            -1 indicates noise (HDBSCAN only).
        """
        n_samples = embeddings.shape[0]

        if self.method == "hdbscan":
            labels = self._hdbscan_cluster(embeddings, n_samples)
        else:
            labels = self._kmeans_cluster(embeddings, n_samples)

        self._labels = labels

        # Compute and log metrics
        unique_labels = set(labels) - {-1}
        logger.info(f"Clustering complete: {len(unique_labels)} clusters found")

        if len(unique_labels) >= 2 and n_samples > len(unique_labels):
            try:
                score = silhouette_score(
                    embeddings, labels, sample_size=min(1000, n_samples)
                )
                logger.info(f"Silhouette score: {score:.4f}")
            except Exception:
                pass

        return labels

    def _kmeans_cluster(self, embeddings: np.ndarray, n_samples: int) -> np.ndarray:
        """KMeans clustering."""
        k = min(self.n_clusters, n_samples)
        logger.info(f"Running KMeans with k={k}")

        self._model = KMeans(
            n_clusters=k,
            random_state=self.random_state,
            n_init=10,
            max_iter=300,
        )
        labels = self._model.fit_predict(embeddings)
        return labels

    def _hdbscan_cluster(self, embeddings: np.ndarray, n_samples: int) -> np.ndarray:
        """HDBSCAN density-based clustering."""
        try:
            import hdbscan

            min_size = min(self.min_cluster_size, max(2, n_samples // 10))
            logger.info(f"Running HDBSCAN with min_cluster_size={min_size}")

            self._model = hdbscan.HDBSCAN(
                min_cluster_size=min_size,
                metric="euclidean",
                cluster_selection_method="eom",
            )
            labels = self._model.fit_predict(embeddings)
            return labels

        except ImportError:
            logger.warning("hdbscan not installed, falling back to KMeans")
            return self._kmeans_cluster(embeddings, n_samples)

    def get_cluster_stats(self, embeddings: np.ndarray) -> list[dict]:
        """Compute per-cluster statistics.

        Returns:
            List of dicts with cluster_id, size, mean, std info.
        """
        if self._labels is None:
            raise RuntimeError("Must call fit_predict() first")

        stats = []
        unique_labels = sorted(set(self._labels) - {-1})

        for label in unique_labels:
            mask = self._labels == label
            cluster_embeddings = embeddings[mask]

            stats.append({
                "cluster_id": int(label),
                "size": int(mask.sum()),
                "mean_norm": float(np.linalg.norm(cluster_embeddings.mean(axis=0))),
                "std": float(cluster_embeddings.std()),
            })

        return stats
