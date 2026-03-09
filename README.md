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

```bash
cd backend

# Create virtual environment with uv
uv venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
uv pip install -e .

# Start the API server
python -m app.main
# → API running at http://localhost:8000
# → Docs at http://localhost:8000/docs
```

### 2. Frontend Setup

```bash
cd frontend

npm install
npm run dev
# → Frontend at http://localhost:3000
```

### 3. Docker (Full Stack)

```bash
docker-compose up --build
# → Frontend: http://localhost:3000
# → Backend:  http://localhost:8000
# → MinIO:    http://localhost:9001
```

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/datasets/upload` | Upload image dataset |
| `GET` | `/api/datasets` | List all datasets |
| `GET` | `/api/datasets/{id}` | Get dataset details |
| `POST` | `/api/datasets/{id}/process` | Trigger ML pipeline |
| `GET` | `/api/datasets/{id}/clusters` | Get cluster info |
| `GET` | `/api/datasets/{id}/duplicates` | Get duplicate groups |
| `GET` | `/api/datasets/{id}/outliers` | Get outlier images |
| `POST` | `/api/search/similar` | Similarity search |
| `GET` | `/api/embeddings/map` | Get UMAP coordinates |
| `GET` | `/api/health` | Health check |

## 🧠 ML Pipeline

```
Upload Images
    ↓
Preprocess (resize, normalize)
    ↓
Extract Embeddings (DINOv2 / SimCLR / MoCo)
    ↓
Build FAISS Index (cosine similarity)
    ↓
┌─────────────┬──────────────┬──────────────┐
│  Clustering │  Duplicates  │   Outliers   │
│  KMeans /   │  Cosine sim  │  IsoForest + │
│  HDBSCAN    │  > 0.98      │  k-NN dist   │
└─────────────┴──────────────┴──────────────┘
    ↓
UMAP 3D Projection
    ↓
Store results in DB
```

## 🎨 Frontend Pages

| Page | Description |
|------|-------------|
| **Dashboard** | Stats overview, quick actions |
| **Datasets** | Upload, list, manage datasets |
| **Dataset Detail** | Tabbed view: images, clusters, duplicates, outliers |
| **Embedding Galaxy** | Interactive 3D point cloud (React Three Fiber) |
| **Similarity Search** | Upload image → find matches |
| **Duplicates Viewer** | Grouped duplicate galleries |
| **Outlier Viewer** | Anomaly-scored image cards |
| **Cluster Explorer** | Color-coded cluster galleries |

## ⚙️ Configuration

Key environment variables (see `backend/.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `DEFAULT_MODEL` | `dinov2` | SSL model (dinov2/simclr/moco) |
| `DINOV2_VARIANT` | `vitb14` | ViT variant (vits14/vitb14/vitl14) |
| `DEVICE` | `cpu` | Compute device (cpu/cuda) |
| `DUPLICATE_THRESHOLD` | `0.98` | Min cosine sim for duplicates |
| `OUTLIER_CONTAMINATION` | `0.05` | Expected outlier fraction |
| `BATCH_SIZE` | `32` | Inference batch size |

## 📦 Tech Stack

**Backend**: FastAPI, SQLAlchemy, Celery, Redis, PostgreSQL  
**ML**: PyTorch, DINOv2, FAISS, UMAP, scikit-learn, HDBSCAN  
**Frontend**: Next.js 14, TypeScript, TailwindCSS, React Three Fiber, Zustand, React Query  
**Infra**: Docker, Docker Compose, Kubernetes-ready

## 📄 License

MIT
