/**
 * VisionCurator API client.
 * Handles all communication with the FastAPI backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

/** Generic fetch wrapper with error handling. */
async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      ...(options?.headers || {}),
    },
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API Error: ${res.status}`);
  }

  return res.json();
}

// ── Types ────────────────────────────────────────────────────────────────────

export interface Dataset {
  id: string;
  name: string;
  description: string | null;
  status: "pending" | "processing" | "completed" | "failed";
  image_count: number;
  processed_count: number;
  cluster_count: number;
  duplicate_count: number;
  outlier_count: number;
  duplicate_percentage: number;
  model_name: string;
  embedding_dim: number;
  version: number;
  stats: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface ImageRecord {
  id: string;
  dataset_id: string;
  filename: string;
  filepath: string;
  file_size: number;
  width: number | null;
  height: number | null;
  cluster_id: number | null;
  cluster_label: string | null;
  is_duplicate: boolean;
  duplicate_group_id: string | null;
  is_outlier: boolean;
  outlier_score: number | null;
  umap_x: number | null;
  umap_y: number | null;
  umap_z: number | null;
  created_at: string;
}

export interface ClusterInfo {
  cluster_id: number;
  size: number;
  label: string | null;
  centroid_x: number | null;
  centroid_y: number | null;
  centroid_z: number | null;
  sample_images: ImageRecord[];
}

export interface DuplicateGroup {
  group_id: string;
  images: ImageRecord[];
  similarity: number;
}

export interface EmbeddingPoint {
  image_id: string;
  filename: string;
  x: number;
  y: number;
  z: number;
  cluster_id: number | null;
  is_outlier: boolean;
  is_duplicate: boolean;
}

export interface DashboardStats {
  total_datasets: number;
  total_images: number;
  total_duplicates: number;
  total_outliers: number;
  total_clusters: number;
  processing_datasets: number;
  completed_datasets: number;
  storage_used_mb: number;
}

// ── API Functions ────────────────────────────────────────────────────────────

export const api = {
  // Dashboard
  getDashboardStats: () => apiFetch<DashboardStats>("/dashboard/stats"),

  // Datasets
  listDatasets: (skip = 0, limit = 20) =>
    apiFetch<{ datasets: Dataset[]; total: number }>(
      `/datasets?skip=${skip}&limit=${limit}`
    ),

  getDataset: (id: string) => apiFetch<Dataset>(`/datasets/${id}`),

  uploadDataset: async (name: string, description: string, files: File[]) => {
    const formData = new FormData();
    files.forEach((f) => formData.append("files", f));
    return apiFetch<Dataset>(
      `/datasets/upload?name=${encodeURIComponent(name)}&description=${encodeURIComponent(description)}`,
      { method: "POST", body: formData }
    );
  },

  deleteDataset: (id: string) =>
    apiFetch<void>(`/datasets/${id}`, { method: "DELETE" }),

  processDataset: (id: string, config?: Record<string, unknown>) =>
    apiFetch<{ dataset_id: string; status: string }>(
      `/datasets/${id}/process`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config || {}),
      }
    ),

  // Images
  getDatasetImages: (id: string, skip = 0, limit = 50) =>
    apiFetch<{ images: ImageRecord[]; total: number }>(
      `/datasets/${id}/images?skip=${skip}&limit=${limit}`
    ),

  // Clusters
  getDatasetClusters: (id: string) =>
    apiFetch<{ clusters: ClusterInfo[]; total: number }>(
      `/datasets/${id}/clusters`
    ),

  // Duplicates
  getDatasetDuplicates: (id: string) =>
    apiFetch<{ groups: DuplicateGroup[]; total_groups: number; total_duplicates: number }>(
      `/datasets/${id}/duplicates`
    ),

  // Outliers
  getDatasetOutliers: (id: string, skip = 0, limit = 50) =>
    apiFetch<{ outliers: ImageRecord[]; total: number }>(
      `/datasets/${id}/outliers?skip=${skip}&limit=${limit}`
    ),

  // Embeddings
  getEmbeddingMap: (datasetId: string) =>
    apiFetch<{ points: EmbeddingPoint[]; total: number; dimensions: number }>(
      `/embeddings/map?dataset_id=${datasetId}`
    ),

  // Search
  similaritySearch: async (datasetId: string, file: File, topK = 20) => {
    const formData = new FormData();
    formData.append("file", file);
    return apiFetch<{ results: ImageRecord[]; distances: number[] }>(
      `/search/similar?dataset_id=${datasetId}&top_k=${topK}`,
      { method: "POST", body: formData }
    );
  },

  // Health
  health: () => apiFetch<{ status: string }>("/health"),
};
