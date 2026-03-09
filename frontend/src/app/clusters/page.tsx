"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Boxes, Loader2 } from "lucide-react";
import { api, type Dataset, type ClusterInfo } from "@/lib/api";
import { useAppStore } from "@/lib/store";

const CLUSTER_COLORS = [
    "#6366f1", "#ec4899", "#f59e0b", "#22c55e", "#3b82f6",
    "#a855f7", "#06b6d4", "#ef4444", "#84cc16", "#f97316",
];

export default function ClustersPage() {
    const [selectedDatasetId, setSelectedDatasetId] = useState<string | null>(null);
    const [expandedCluster, setExpandedCluster] = useState<number | null>(null);
    const { openImageModal } = useAppStore();

    const { data: datasetsData } = useQuery({
        queryKey: ["datasets"],
        queryFn: () => api.listDatasets(0, 50),
    });

    const { data: clustersData, isLoading } = useQuery({
        queryKey: ["clusters", selectedDatasetId],
        queryFn: () => api.getDatasetClusters(selectedDatasetId!),
        enabled: !!selectedDatasetId,
    });

    const datasets = datasetsData?.datasets?.filter((d: Dataset) => d.status === "completed") || [];
    const clusters = clustersData?.clusters || [];
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2">
                        <Boxes className="text-[var(--success)]" /> Cluster Explorer
                    </h1>
                    <p style={{ color: "var(--text-muted)" }}>
                        Explore semantic groupings discovered by KMeans/HDBSCAN clustering
                    </p>
                </div>
                <select
                    value={selectedDatasetId || ""}
                    onChange={(e) => setSelectedDatasetId(e.target.value || null)}
                    className="px-4 py-2 rounded-xl text-sm outline-none"
                    style={{ background: "var(--bg-card)", border: "1px solid var(--border)", color: "var(--text-primary)" }}
                >
                    <option value="">Select dataset</option>
                    {datasets.map((ds: Dataset) => (
                        <option key={ds.id} value={ds.id}>{ds.name}</option>
                    ))}
                </select>
            </div>

            {!selectedDatasetId ? (
                <div className="glass-card p-16 text-center">
                    <Boxes size={48} className="mx-auto mb-4" style={{ color: "var(--text-muted)" }} />
                    <p style={{ color: "var(--text-muted)" }}>Select a processed dataset to explore clusters</p>
                </div>
            ) : isLoading ? (
                <div className="glass-card p-16 text-center">
                    <Loader2 size={32} className="mx-auto mb-4 animate-spin" style={{ color: "var(--accent)" }} />
                </div>
            ) : (
                <>
                    {/* Overview */}
                    <div className="glass-card p-5">
                        <h3 className="font-semibold mb-3">Cluster Distribution</h3>
                        <div className="flex gap-2 flex-wrap">
                            {clusters.map((c: ClusterInfo) => (
                                <button
                                    key={c.cluster_id}
                                    onClick={() => setExpandedCluster(expandedCluster === c.cluster_id ? null : c.cluster_id)}
                                    className={`px-4 py-2 rounded-xl text-sm font-medium transition-all hover:scale-105 ${expandedCluster === c.cluster_id ? "ring-2 ring-white/30" : ""
                                        }`}
                                    style={{
                                        background: `${CLUSTER_COLORS[c.cluster_id % CLUSTER_COLORS.length]}22`,
                                        color: CLUSTER_COLORS[c.cluster_id % CLUSTER_COLORS.length],
                                        border: `1px solid ${CLUSTER_COLORS[c.cluster_id % CLUSTER_COLORS.length]}44`,
                                    }}
                                >
                                    #{c.cluster_id} • {c.size} images
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Cluster Cards */}
                    <div className="space-y-4">
                        {clusters
                            .filter((c: ClusterInfo) => expandedCluster === null || expandedCluster === c.cluster_id)
                            .map((cluster: ClusterInfo) => {
                                const color = CLUSTER_COLORS[cluster.cluster_id % CLUSTER_COLORS.length];
                                return (
                                    <div key={cluster.cluster_id} className="glass-card p-5">
                                        <div className="flex items-center justify-between mb-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-4 h-4 rounded-full" style={{ background: color }} />
                                                <h3 className="font-semibold text-lg">
                                                    Cluster #{cluster.cluster_id}
                                                </h3>
                                                <span className="badge" style={{ background: `${color}22`, color }}>
                                                    {cluster.size} images
                                                </span>
                                            </div>
                                            {cluster.centroid_x !== null && (
                                                <span className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>
                                                    Centroid: ({cluster.centroid_x?.toFixed(2)}, {cluster.centroid_y?.toFixed(2)})
                                                </span>
                                            )}
                                        </div>

                                        <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
                                            {cluster.sample_images.map((img) => (
                                                <div
                                                    key={img.id}
                                                    onClick={() => openImageModal(img)}
                                                    className="aspect-square rounded-lg overflow-hidden cursor-pointer transition-all hover:scale-105"
                                                    style={{
                                                        background: "var(--bg-secondary)",
                                                        border: `2px solid transparent`,
                                                    }}
                                                    onMouseEnter={(e) => (e.currentTarget.style.borderColor = color)}
                                                    onMouseLeave={(e) => (e.currentTarget.style.borderColor = "transparent")}
                                                >
                                                    <img
                                                        src={`${baseUrl}/uploads/${img.dataset_id}/${img.filename}`}
                                                        alt={img.filename}
                                                        className="w-full h-full object-cover"
                                                        loading="lazy"
                                                    />
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                );
                            })}
                    </div>
                </>
            )}
        </div>
    );
}
