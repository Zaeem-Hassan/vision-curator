<div align="center">
  <h1 align="center">🔬 VisionCurator</h1>
  <p align="center">
    <strong>Self-Supervised Dataset Intelligence Platform for Computer Vision</strong>
    <br />
    A powerful tool to automatically analyze, clean, and explore image datasets using state-of-the-art AI.
  </p>
</div>

---

## 🚀 Overview

**VisionCurator** is an end-to-end platform for computer vision engineers and data scientists to manage and curate raw image datasets before labeling. 

Instead of manually sifting through thousands of images, VisionCurator uses self-supervised learning models (like **ResNet50**, **DINOv2**, **SimCLR**) to understand the semantic meaning of your images. It automatically detects duplicates, flags anomalous outliers, groups similar images into clusters, and lets you explore your entire dataset in an interactive 3D galaxy.

When you're done, use **Smart Export** to download a perfectly balanced, duplicate-free dataset ready for your labeling pipeline.

<br>

## ✨ Key Features

- **🧠 Auto-Embedding Extraction**: Uses PyTorch and torchvision/SSL models to extract rich feature vectors from your images automatically.
- **📁 Bulk Folder Uploads**: Upload entire directory trees of images right from your browser; the system handles subfolders seamlessly.
- **👯‍♂️ Duplicate Detection**: Identifies exact and near-duplicate images using highly optimized cosine-similarity matching.
- **🚨 Outlier Detection**: Flags rare edge-cases, anomalies, and corrupted images using Isolation Forests and k-NN distance scoring.
- **📦 Semantic Clustering**: Groups visually similar images together using KMeans to help you understand your data distribution.
- **🌌 3D Galaxy View**: Explore your dataset interactively in a 3D UMAP point cloud rendered with React Three Fiber.
- **🔍 Vector Search**: Built-in visual search powered by FAISS. Upload an image to instantly find the most visually similar images in your dataset.
- **🎯 Smart Export**: Stop labeling redundant data. Export a perfectly balanced ZIP file that prioritizes high-value outliers, ensures equal representation across clusters, and excludes duplicates.
- **⚡ High Performance**: Parallelized image processing, optimized batch inference with `torch.inference_mode()`, and SQLite/SQLAlchemy backend.

<br>

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Machine Learning**: PyTorch, Torchvision, scikit-learn, UMAP-learn, FAISS
- **Database**: SQLite / SQLAlchemy ORM (Async)
- **Concurrency**: `asyncio` threads + `ThreadPoolExecutor` for parallel I/O

### Frontend
- **Framework**: Next.js 14 (App Router) + React
- **Styling**: TailwindCSS + Lucide Icons + Glassmorphism UI
- **State Management**: Zustand + React Query (@tanstack/react-query)
- **3D Rendering**: Three.js + React Three Fiber (@react-three/fiber)

<br>

## 🚀 Quick Start (Local Development)

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/vision-curator.git
cd vision-curator
```

### 2. Backend Setup
We recommend using [uv](https://github.com/astral-sh/uv) for fast Python dependency management.

```bash
cd backend

# Create and activate a virtual environment
uv venv
# Windows: .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate

# Install dependencies
uv pip install -e .

# Start the FastAPI server (runs on http://localhost:8000)
python -m app.main
```

### 3. Frontend Setup
Open a new terminal window.

```bash
cd frontend

# Install Node modules
npm install

# Start the Next.js development server (runs on http://localhost:3000)
npm run dev
```

### 4. Open the App
Navigate to **http://localhost:3000** in your browser.

<br>

## 🏗️ Architecture overview

```text
┌──────────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js / React)                    │
│  Dashboard │ Galaxy 3D │ Search │ Duplicates │ Outliers │ Curves │
├──────────────────────────────────────────────────────────────────┤
│                       FastAPI Backend                            │
│           REST API │ File Upload │ ZIP Export                    │
├──────────────────────────────────────────────────────────────────┤
│                      ML Pipeline Services                        │
│  ResNet50 │ DINOv2 │ FAISS │ UMAP │ KMeans │ Isolation Forest    │
├──────────────────────────────────────────────────────────────────┤
│       ThreadPoolExecutor (Parallel I/O)  │  SQLite Database      │
└──────────────────────────────────────────────────────────────────┘
```

The pipeline runs entirely locally by default. Images are saved to `backend/data/uploads`, and the database is stored in `backend/data/visioncurator.db`.

<br>

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.
