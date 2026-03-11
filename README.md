# 🔬 VisionCurator

**Self-Supervised Dataset Intelligence Platform for Computer Vision**

> Automatically analyze image datasets using SSL models, detect duplicates/outliers, cluster semantically, and explore your data in an interactive 3D embedding galaxy.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js / React)                    │
│  Dashboard │ Galaxy 3D │ Search │ Duplicates │ Outliers │ Clusters │
├──────────────────────────────────────────────────────────────────┤
│                       FastAPI Backend                            │
│           REST API │ File Upload │ Static Serving                │
├──────────────────────────────────────────────────────────────────┤
│                      ML Pipeline Services                        │
│  DINOv2 │ SimCLR │ MoCo │ FAISS │ UMAP │ KMeans │ HDBSCAN      │
├──────────────────────────────────────────────────────────────────┤
│  Celery Workers  │  Redis (Queue)  │  PostgreSQL  │  MinIO/S3   │
└──────────────────────────────────────────────────────────────────┘
```

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Embedding Generation** | DINOv2, SimCLR, MoCo self-supervised models |
| **Vector Search** | FAISS-powered similarity search (<50ms latency) |
| **Duplicate Detection** | Cosine similarity grouping (threshold 0.98) |
| **Outlier Detection** | Isolation Forest + k-NN ensemble |
| **Clustering** | KMeans / HDBSCAN semantic grouping |
| **3D Galaxy** | React Three Fiber interactive point cloud |
| **Dataset Versioning** | Track dataset evolution over time |
| **Background Processing** | Celery async pipeline for large datasets |

## 🗂️ Project Structure

```
visioncurator/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI route handlers
│   │   │   ├── datasets.py   # Dataset CRUD + processing
│   │   │   ├── search.py     # Similarity search
│   │   │   └── embeddings.py # Embedding map endpoints
│   │   ├── models/           # SQLAlchemy models + Pydantic schemas
│   │   ├── services/         # Processing pipeline, Celery tasks
│   │   ├── config.py         # Pydantic settings
│   │   ├── database.py       # Async SQLAlchemy setup
│   │   └── main.py           # FastAPI entry point
│   └── pyproject.toml
├── ml/
│   ├── embedding_models/     # DINOv2, SimCLR, MoCo wrappers
│   ├── embeddings/           # FAISS index, UMAP/t-SNE
│   ├── clustering/           # KMeans, HDBSCAN
│   ├── outlier_detection/    # Isolation Forest, k-NN, duplicates
│   └── preprocessing/       # Image loading & transforms
├── frontend/
│   └── src/
│       ├── app/              # Next.js pages (App Router)
│       ├── components/       # Sidebar, ImageModal, ClientLayout
│       └── lib/              # API client, Zustand store, providers
├── infrastructure/
│   ├── docker/               # Dockerfiles
│   └── kubernetes/           # K8s deployment manifests
├── docker-compose.yml
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- [uv](https://github.com/astral-sh/uv) (Python package manager)

### 1. Backend Setup
