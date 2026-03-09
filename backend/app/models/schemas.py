"""Pydantic request / response schemas."""

from __future__ import annotations

import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Dataset Schemas ──────────────────────────────────────────────────────────


class DatasetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    model_name: str = "dinov2"


class DatasetResponse(BaseModel):
    id: str
    name: str
    description: str | None
    status: str
    image_count: int
    processed_count: int
    cluster_count: int
    duplicate_count: int
    outlier_count: int
    duplicate_percentage: float
    model_name: str
    embedding_dim: int
    version: int
    stats: dict[str, Any] | None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class DatasetListResponse(BaseModel):
    datasets: list[DatasetResponse]
    total: int


# ── Image Schemas ────────────────────────────────────────────────────────────


class ImageResponse(BaseModel):
    id: str
    dataset_id: str
    filename: str
    filepath: str
    file_size: int
    width: int | None
    height: int | None
    cluster_id: int | None
    cluster_label: str | None
    is_duplicate: bool
    duplicate_group_id: str | None
    is_outlier: bool
    outlier_score: float | None
    umap_x: float | None
    umap_y: float | None
    umap_z: float | None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class ImageListResponse(BaseModel):
    images: list[ImageResponse]
    total: int


# ── Cluster Schemas ──────────────────────────────────────────────────────────


class ClusterInfo(BaseModel):
    cluster_id: int
    size: int
    label: str | None = None
    centroid_x: float | None = None
    centroid_y: float | None = None
    centroid_z: float | None = None
    sample_images: list[ImageResponse] = []


class ClusterListResponse(BaseModel):
    clusters: list[ClusterInfo]
    total: int


# ── Duplicate Schemas ────────────────────────────────────────────────────────


class DuplicateGroup(BaseModel):
    group_id: str
    images: list[ImageResponse]
    similarity: float = 0.0


class DuplicateListResponse(BaseModel):
    groups: list[DuplicateGroup]
    total_groups: int
    total_duplicates: int


# ── Outlier Schemas ──────────────────────────────────────────────────────────


class OutlierListResponse(BaseModel):
    outliers: list[ImageResponse]
    total: int


# ── Search Schemas ───────────────────────────────────────────────────────────


class SimilaritySearchResponse(BaseModel):
    query_image: str | None = None
    results: list[ImageResponse]
    distances: list[float]


# ── Embedding Map Schemas ────────────────────────────────────────────────────


class EmbeddingPoint(BaseModel):
    image_id: str
    filename: str
    x: float
    y: float
    z: float = 0.0
    cluster_id: int | None = None
    is_outlier: bool = False
    is_duplicate: bool = False


class EmbeddingMapResponse(BaseModel):
    points: list[EmbeddingPoint]
    total: int
    dimensions: int = 3


# ── Processing Schemas ───────────────────────────────────────────────────────


class ProcessingRequest(BaseModel):
    model_name: str = "dinov2"
    cluster_method: str = "kmeans"
    n_clusters: int = 10
    detect_duplicates: bool = True
    detect_outliers: bool = True
    generate_map: bool = True


class ProcessingStatus(BaseModel):
    dataset_id: str
    status: str
    progress: float = 0.0
    current_step: str = ""
    message: str = ""


# ── Dashboard Schemas ────────────────────────────────────────────────────────


class DashboardStats(BaseModel):
    total_datasets: int
    total_images: int
    total_duplicates: int
    total_outliers: int
    total_clusters: int
    processing_datasets: int
    completed_datasets: int
    storage_used_mb: float = 0.0
