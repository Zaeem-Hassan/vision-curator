"""Outlier detection for image embeddings.

Combines Isolation Forest and k-NN distance scoring to identify
anomalous images in a dataset.
"""

import numpy as np
from loguru import logger
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import NearestNeighbors


class OutlierDetector:
    """Detect outlier images using ensemble of Isolation Forest + k-NN.

    Images with high anomaly scores from either method are flagged as outliers.

    Attributes:
        contamination: Expected fraction of outliers (0.0 - 0.5).
        n_neighbors: Number of neighbors for k-NN distance scoring.
        method: Detection method ('ensemble', 'isolation_forest', 'knn').
    """

    def __init__(
        self,
        contamination: float = 0.05,
        n_neighbors: int = 20,
        method: str = "ensemble",
        random_state: int = 42,
    ):
        self.contamination = max(0.01, min(contamination, 0.49))
        self.n_neighbors = n_neighbors
        self.method = method
        self.random_state = random_state

    def detect(
        self, embeddings: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """Detect outliers in the embedding space.

        Args:
            embeddings: Array of shape [N, D].

        Returns:
            Tuple of (scores, mask):
                - scores: Anomaly score per image [N]. Higher = more anomalous.
                - mask: Boolean array [N], True = outlier.
        """
        n_samples = embeddings.shape[0]
        neighbors = min(self.n_neighbors, n_samples - 1)

        if self.method == "isolation_forest":
            scores, mask = self._isolation_forest(embeddings)
        elif self.method == "knn":
            scores, mask = self._knn_distance(embeddings, neighbors)
        else:
            # Ensemble: combine both methods
            if_scores, _ = self._isolation_forest(embeddings)
            knn_scores, _ = self._knn_distance(embeddings, neighbors)

            # Normalize scores to [0, 1] and average
            if_norm = self._normalize(if_scores)
            knn_norm = self._normalize(knn_scores)
            scores = (if_norm + knn_norm) / 2.0

            # Threshold at the contamination percentile
            threshold = np.percentile(scores, (1 - self.contamination) * 100)
            mask = scores >= threshold

        n_outliers = int(mask.sum())
        logger.info(f"Outlier detection: {n_outliers}/{n_samples} flagged ({n_outliers / n_samples * 100:.1f}%)")
        return scores, mask

    def _isolation_forest(
        self, embeddings: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """Isolation Forest anomaly detection."""
        logger.info("Running Isolation Forest")
        iso = IsolationForest(
            contamination=self.contamination,
            random_state=self.random_state,
            n_estimators=100,
        )
        predictions = iso.fit_predict(embeddings)
        mask = predictions == -1
        scores = -iso.score_samples(embeddings)  # Higher = more anomalous
        return scores, mask

    def _knn_distance(
        self, embeddings: np.ndarray, n_neighbors: int
    ) -> tuple[np.ndarray, np.ndarray]:
        """k-NN distance based outlier scoring."""
        logger.info(f"Running k-NN distance (k={n_neighbors})")
        nn = NearestNeighbors(n_neighbors=n_neighbors, metric="cosine")
        nn.fit(embeddings)
        distances, _ = nn.kneighbors(embeddings)

        # Average distance to k neighbors as the anomaly score
        scores = distances.mean(axis=1)

        # Threshold at contamination percentile
        threshold = np.percentile(scores, (1 - self.contamination) * 100)
        mask = scores >= threshold

        return scores, mask

    @staticmethod
    def _normalize(scores: np.ndarray) -> np.ndarray:
        """Min-max normalize scores to [0, 1]."""
        s_min, s_max = scores.min(), scores.max()
        if s_max - s_min < 1e-8:
            return np.zeros_like(scores)
        return (scores - s_min) / (s_max - s_min)
