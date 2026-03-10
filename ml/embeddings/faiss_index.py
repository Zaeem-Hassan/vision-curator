"""FAISS vector index manager.

Handles building, saving, loading, and querying FAISS indices
for fast approximate nearest-neighbor search on image embeddings.
"""

from pathlib import Path

import faiss
import numpy as np
from loguru import logger


class FAISSIndex:
    """Wrapper around FAISS for cosine-similarity vector search.

    Uses IndexFlatIP (inner product on L2-normalized vectors) for
    exact cosine similarity search. For datasets >500k, you can
    swap to IndexIVFFlat or IndexHNSW for approximate search.

    Attributes:
        dim: Dimensionality of embedding vectors.
        index: The underlying FAISS index.
    """

    def __init__(self, dim: int = 768):
        self.dim = dim
        self.index: faiss.Index | None = None
        self._n_vectors = 0

    def build(self, embeddings: np.ndarray) -> None:
        """Build a FAISS index from embeddings.

        Normalizes vectors for cosine similarity, then adds to IndexFlatIP.

        Args:
            embeddings: Array of shape [N, D].
        """
        embeddings = np.ascontiguousarray(embeddings, dtype=np.float32)
        faiss.normalize_L2(embeddings)

        self.index = faiss.IndexFlatIP(self.dim)
        self.index.add(embeddings)
        self._n_vectors = embeddings.shape[0]

        logger.info(f"FAISS index built: {self._n_vectors} vectors, dim={self.dim}")

    def search(self, query: np.ndarray, top_k: int = 20) -> tuple[np.ndarray, np.ndarray]:
        """Search for nearest neighbors.

        Args:
            query: Query vector(s) of shape [Q, D].
            top_k: Number of nearest neighbors to return.

        Returns:
            Tuple of (distances, indices) each of shape [Q, top_k].
        """
        if self.index is None:
            raise RuntimeError("Index not built. Call build() or load() first.")

        query = np.ascontiguousarray(query, dtype=np.float32)
        faiss.normalize_L2(query)
        distances, indices = self.index.search(query, top_k)
        return distances, indices

    def add(self, embeddings: np.ndarray) -> None:
        """Add new vectors to an existing index.

        Args:
            embeddings: Array of shape [N, D].
        """
        if self.index is None:
            self.build(embeddings)
            return

        embeddings = np.ascontiguousarray(embeddings, dtype=np.float32)
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings)
        self._n_vectors += embeddings.shape[0]
        logger.info(f"Added {embeddings.shape[0]} vectors — total: {self._n_vectors}")

    def save(self, path: str) -> None:
        """Save index to disk."""
        if self.index is None:
            raise RuntimeError("No index to save")
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, path)
        logger.info(f"FAISS index saved to {path}")

    def load(self, path: str) -> None:
        """Load index from disk."""
        if not Path(path).exists():
            raise FileNotFoundError(f"Index file not found: {path}")
        self.index = faiss.read_index(path)
        self._n_vectors = self.index.ntotal
        logger.info(f"FAISS index loaded: {self._n_vectors} vectors")

    @property
    def size(self) -> int:
        """Number of vectors in the index."""
        return self._n_vectors
