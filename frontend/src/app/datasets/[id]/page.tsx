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
} from "lucide-react";
import { api, type ImageRecord } from "@/lib/api";
import { useAppStore } from "@/lib/store";

export default function DatasetDetailPage() {
    const params = useParams();
    const datasetId = params.id as string;
    const [activeTab, setActiveTab] = useState<"images" | "clusters" | "duplicates" | "outliers">("images");
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
                        <Link
                            href={`/galaxy?dataset=${datasetId}`}
                            className="flex items-center gap-2 px-4 py-2 rounded-xl text-white text-sm font-medium"
                            style={{ background: "var(--gradient-2)" }}
                        >
                            <Orbit size={14} /> View Galaxy
                        </Link>
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
    const url = `${baseUrl}/uploads/${datasetId}/${image.filename}`;
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
