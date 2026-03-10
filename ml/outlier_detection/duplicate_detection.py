"""Duplicate detection for image embeddings.

Groups images into duplicate clusters based on cosine similarity
thresholding in the embedding space.
"""

import uuid

import numpy as np
from loguru import logger


class DuplicateDetector:
    """Detect near-duplicate images using cosine similarity.

    Uses pairwise cosine similarity to group images that exceed
    the similarity threshold into duplicate groups.

    Attributes:
        threshold: Minimum cosine similarity to consider duplicates (0.0 - 1.0).
    """

    def __init__(self, threshold: float = 0.98):
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"Threshold must be in [0, 1], got {threshold}")
        self.threshold = threshold

    def detect(self, embeddings: np.ndarray) -> dict[str, list[int]]:
        """Find duplicate groups in embeddings.

        Args:
            embeddings: Array of shape [N, D].

        Returns:
            Dict mapping group_id → list of image indices that are duplicates.
            Each group has at least 2 members.
        """
        n = embeddings.shape[0]
        logger.info(f"Detecting duplicates among {n} images (threshold={self.threshold})")

        # Normalize embeddings for cosine similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms < 1e-8, 1.0, norms)
        normalized = np.ascontiguousarray(embeddings / norms, dtype=np.float32)

        assigned: set[int] = set()
        groups: dict[str, list[int]] = {}

        chunk_size = 1000  # Process 1000 rows at a time

        for start in range(0, n, chunk_size):
            end = min(start + chunk_size, n)
            sim_chunk = normalized[start:end] @ normalized.T  # [chunk, N]

            for local_i in range(end - start):
                global_i = start + local_i
                if global_i in assigned:
                    continue

                similarities = sim_chunk[local_i]
                similar_indices = np.where(
                    (similarities >= self.threshold)
                    & (np.arange(n) != global_i)
                    & (np.arange(n) > global_i)
                )[0]

                if len(similar_indices) > 0:
                    group_id = str(uuid.uuid4())
                    group_members = [global_i] + similar_indices.tolist()
                    groups[group_id] = group_members
                    assigned.update(group_members)

        total_dups = sum(len(g) for g in groups.values())
        logger.info(f"Found {len(groups)} duplicate groups ({total_dups} images)")
        return groups
