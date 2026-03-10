"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { useState } from "react";
import Link from "next/link";
import {
    ArrowLeft,
    Play,
    Boxes,
    Copy,
    AlertTriangle,
    Image as ImageIcon,
    Orbit,
    Loader2,
    Download,
    X,
} from "lucide-react";
import { api, type ImageRecord } from "@/lib/api";
import { useAppStore } from "@/lib/store";

export default function DatasetDetailPage() {
    const params = useParams();
    const datasetId = params.id as string;
    const [activeTab, setActiveTab] = useState<"images" | "clusters" | "duplicates" | "outliers">("images");
    const [isExportModalOpen, setIsExportModalOpen] = useState(false);
    const [exportSize, setExportSize] = useState<number>(100);
    const queryClient = useQueryClient();

    const { data: dataset, isLoading } = useQuery({
        queryKey: ["dataset", datasetId],
        queryFn: () => api.getDataset(datasetId),
    });

    const { data: imagesData } = useQuery({
        queryKey: ["dataset-images", datasetId],
        queryFn: () => api.getDatasetImages(datasetId, 0, 100),
        enabled: activeTab === "images",
    });

    const { data: clustersData } = useQuery({
        queryKey: ["dataset-clusters", datasetId],
        queryFn: () => api.getDatasetClusters(datasetId),
        enabled: activeTab === "clusters",
    });

    const { data: duplicatesData } = useQuery({
        queryKey: ["dataset-duplicates", datasetId],
        queryFn: () => api.getDatasetDuplicates(datasetId),
        enabled: activeTab === "duplicates",
    });

    const { data: outliersData } = useQuery({
        queryKey: ["dataset-outliers", datasetId],
        queryFn: () => api.getDatasetOutliers(datasetId),
        enabled: activeTab === "outliers",
    });

    const processMutation = useMutation({
        mutationFn: () => api.processDataset(datasetId),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ["dataset", datasetId] }),
    });

    const { openImageModal } = useAppStore();

    if (isLoading) {
        return <div className="flex items-center gap-2"><Loader2 className="animate-spin" /> Loading dataset...</div>;
    }

    if (!dataset) return <div>Dataset not found</div>;

    const tabs = [
        { key: "images", label: "Images", icon: ImageIcon, count: dataset.image_count },
        { key: "clusters", label: "Clusters", icon: Boxes, count: dataset.cluster_count },
        { key: "duplicates", label: "Duplicates", icon: Copy, count: dataset.duplicate_count },
        { key: "outliers", label: "Outliers", icon: AlertTriangle, count: dataset.outlier_count },
    ] as const;

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-start justify-between">
                <div>
                    <Link href="/datasets" className="flex items-center gap-1 text-sm mb-2 transition-colors hover:text-[var(--accent)]" style={{ color: "var(--text-muted)" }}>
                        <ArrowLeft size={14} /> Back to Datasets
                    </Link>
                    <h1 className="text-2xl font-bold">{dataset.name}</h1>
                    {dataset.description && <p className="mt-1" style={{ color: "var(--text-muted)" }}>{dataset.description}</p>}
                </div>

                <div className="flex gap-2">
                    {dataset.status === "pending" && (
                        <button
                            onClick={() => processMutation.mutate()}
                            className="flex items-center gap-2 px-4 py-2 rounded-xl text-white text-sm font-medium"
                            style={{ background: "var(--accent)" }}
                        >
                            <Play size={14} /> Process
                        </button>
                    )}
                    {dataset.status === "completed" && (
                        <>
                            <button
                                onClick={() => setIsExportModalOpen(true)}
                                className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-colors"
                                style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)", color: "var(--text-primary)" }}
                            >
                                <Download size={14} /> Export
                            </button>
                            <Link
                                href={`/galaxy?dataset=${datasetId}`}
                                className="flex items-center gap-2 px-4 py-2 rounded-xl text-white text-sm font-medium"
                                style={{ background: "var(--gradient-2)" }}
                            >
                                <Orbit size={14} /> View Galaxy
                            </Link>
                        </>
                    )}
                </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                <MiniStat label="Status" value={dataset.status} badgeClass={`badge-${dataset.status === "completed" ? "success" : dataset.status === "processing" ? "processing" : "info"}`} />
                <MiniStat label="Images" value={dataset.image_count.toLocaleString()} />
                <MiniStat label="Clusters" value={dataset.cluster_count.toString()} />
                <MiniStat label="Duplicates" value={`${dataset.duplicate_percentage.toFixed(1)}%`} />
                <MiniStat label="Model" value={dataset.model_name.toUpperCase()} />
            </div>

            {/* Tabs */}
            <div className="flex gap-1 p-1 rounded-xl" style={{ background: "var(--bg-secondary)" }}>
                {tabs.map((tab) => (
                    <button
                        key={tab.key}
                        onClick={() => setActiveTab(tab.key)}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === tab.key ? "text-white" : ""
                            }`}
                        style={{
                            background: activeTab === tab.key ? "var(--bg-hover)" : "transparent",
                            color: activeTab === tab.key ? "var(--text-primary)" : "var(--text-muted)",
                        }}
                    >
                        <tab.icon size={14} />
                        {tab.label}
                        <span className="text-xs opacity-60">({tab.count})</span>
                    </button>
                ))}
            </div>

            {/* Tab Content */}
            <div>
                {activeTab === "images" && (
                    <ImageGrid
                        images={imagesData?.images || []}
                        datasetId={datasetId}
                        onImageClick={openImageModal}
                    />
                )}
                {activeTab === "clusters" && (
                    <div className="space-y-4">
                        {(clustersData?.clusters || []).map((cluster) => (
                            <div key={cluster.cluster_id} className="glass-card p-5">
                                <div className="flex items-center justify-between mb-3">
                                    <h3 className="font-semibold">Cluster #{cluster.cluster_id}</h3>
                                    <span className="text-sm" style={{ color: "var(--text-muted)" }}>{cluster.size} images</span>
                                </div>
                                <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
                                    {cluster.sample_images.map((img) => (
                                        <ImageThumb key={img.id} image={img} datasetId={datasetId} onClick={() => openImageModal(img)} />
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
                {activeTab === "duplicates" && (
                    <div className="space-y-4">
                        {(duplicatesData?.groups || []).map((group) => (
                            <div key={group.group_id} className="glass-card p-5">
                                <div className="flex items-center justify-between mb-3">
                                    <h3 className="font-semibold flex items-center gap-2">
                                        <Copy size={16} style={{ color: "var(--warning)" }} />
                                        Duplicate Group
                                    </h3>
                                    <span className="text-sm" style={{ color: "var(--text-muted)" }}>{group.images.length} images</span>
                                </div>
                                <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
                                    {group.images.map((img) => (
                                        <ImageThumb key={img.id} image={img} datasetId={datasetId} onClick={() => openImageModal(img)} />
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
                {activeTab === "outliers" && (
                    <ImageGrid
                        images={outliersData?.outliers || []}
                        datasetId={datasetId}
                        onImageClick={openImageModal}
                    />
                )}
            </div>

            {/* Export Modal */}
            {isExportModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                    <div className="w-full max-w-md p-6 rounded-2xl relative" style={{ background: "var(--bg-primary)", border: "1px solid var(--border)" }}>
                        <button
                            onClick={() => setIsExportModalOpen(false)}
                            className="absolute top-4 right-4 p-2 rounded-full hover:bg-white/10 transition-colors"
                        >
                            <X size={16} />
                        </button>
                        
                        <h2 className="text-xl font-bold mb-1">Smart Export</h2>
                        <p className="text-sm mb-6" style={{ color: "var(--text-muted)" }}>
                            Downloads a perfectly balanced dataset for labeling. Includes all outliers (high priority edge-cases) and divides the remaining quota equally among all clusters.
                        </p>

                        <div className="mb-6">
                            <label className="block text-sm font-medium mb-2" style={{ color: "var(--text-primary)" }}>
                                Target Dataset Size (Images)
                            </label>
                            <input
                                type="number"
                                min="1"
                                max={dataset.image_count}
                                value={exportSize}
                                onChange={(e) => setExportSize(parseInt(e.target.value) || 100)}
                                className="w-full px-4 py-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-[var(--accent)]"
                                style={{ background: "var(--bg-secondary)", color: "var(--text-primary)", border: "1px solid var(--border)" }}
                            />
                            <p className="text-xs mt-2" style={{ color: "var(--text-muted)" }}>Max available: {dataset.image_count}</p>
                        </div>

                        <div className="flex justify-end gap-3">
                            <button
                                onClick={() => setIsExportModalOpen(false)}
                                className="px-4 py-2 rounded-xl text-sm font-medium"
                                style={{ background: "var(--bg-secondary)" }}
                            >
                                Cancel
                            </button>
                            <button
                                onClick={() => {
                                    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
                                    window.open(`${baseUrl}/datasets/${datasetId}/export?max_images=${exportSize}`, '_blank');
                                    setIsExportModalOpen(false);
                                }}
                                className="flex items-center gap-2 px-5 py-2 rounded-xl text-white text-sm font-medium"
                                style={{ background: "var(--accent)" }}
                            >
                                <Download size={16} /> Download ZIP
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

function MiniStat({ label, value, badgeClass }: { label: string; value: string; badgeClass?: string }) {
    return (
        <div className="glass-card p-3 text-center">
            <p className="text-xs mb-1" style={{ color: "var(--text-muted)" }}>{label}</p>
            {badgeClass ? <span className={`badge ${badgeClass}`}>{value}</span> : <p className="font-bold">{value}</p>}
        </div>
    );
}

function ImageGrid({ images, datasetId, onImageClick }: { images: ImageRecord[]; datasetId: string; onImageClick: (img: ImageRecord) => void }) {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    return (
        <div className="grid grid-cols-3 md:grid-cols-5 lg:grid-cols-7 gap-2">
            {images.map((img) => (
                <ImageThumb key={img.id} image={img} datasetId={datasetId} onClick={() => onImageClick(img)} />
            ))}
        </div>
    );
}

function ImageThumb({ image, datasetId, onClick }: { image: ImageRecord; datasetId: string; onClick: () => void }) {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    // filepath is stored as a Windows path like:
    //   data\uploads\<datasetId>\cat\cat_0001.png
    // We need: http://localhost:8000/uploads/<datasetId>/cat/cat_0001.png
    const relativePath = (image.filepath || "")
        .replace(/\\/g, "/")          // normalise Windows backslashes
        .replace(/^.*?uploads\//, ""); // strip everything up to and including "uploads/"
    const url = relativePath
        ? `${baseUrl}/uploads/${relativePath}`
        : `${baseUrl}/uploads/${datasetId}/${image.filename}`; // fallback
    return (
        <div
            onClick={onClick}
            className="aspect-square rounded-lg overflow-hidden cursor-pointer transition-all hover:scale-105 hover:ring-2 hover:ring-[var(--accent)] relative group"
            style={{ background: "var(--bg-secondary)" }}
        >
            <img src={url} alt={image.filename} className="w-full h-full object-cover" loading="lazy" />
            {(image.is_duplicate || image.is_outlier) && (
                <div className="absolute top-1 right-1 flex gap-1">
                    {image.is_duplicate && <div className="w-2 h-2 rounded-full" style={{ background: "var(--warning)" }} />}
                    {image.is_outlier && <div className="w-2 h-2 rounded-full" style={{ background: "var(--danger)" }} />}
                </div>
            )}
        </div>
    );
}
