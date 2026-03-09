"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Copy, Loader2 } from "lucide-react";
import { api, type Dataset } from "@/lib/api";
import { useAppStore } from "@/lib/store";

export default function DuplicatesPage() {
    const [selectedDatasetId, setSelectedDatasetId] = useState<string | null>(null);
    const { openImageModal } = useAppStore();

    const { data: datasetsData } = useQuery({
        queryKey: ["datasets"],
        queryFn: () => api.listDatasets(0, 50),
    });

    const { data: dupsData, isLoading } = useQuery({
        queryKey: ["duplicates", selectedDatasetId],
        queryFn: () => api.getDatasetDuplicates(selectedDatasetId!),
        enabled: !!selectedDatasetId,
    });

    const datasets = datasetsData?.datasets?.filter((d: Dataset) => d.status === "completed") || [];
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2">
                        <Copy className="text-[var(--warning)]" /> Duplicates Viewer
                    </h1>
                    <p style={{ color: "var(--text-muted)" }}>
                        View near-duplicate image groups detected by cosine similarity
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
                    <Copy size={48} className="mx-auto mb-4" style={{ color: "var(--text-muted)" }} />
                    <p style={{ color: "var(--text-muted)" }}>Select a processed dataset to view duplicates</p>
                </div>
            ) : isLoading ? (
                <div className="glass-card p-16 text-center">
                    <Loader2 size={32} className="mx-auto mb-4 animate-spin" style={{ color: "var(--accent)" }} />
                </div>
            ) : (
                <>
                    {/* Summary */}
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                        <div className="glass-card p-4 text-center">
                            <p className="text-xs" style={{ color: "var(--text-muted)" }}>Groups</p>
                            <p className="text-2xl font-bold">{dupsData?.total_groups || 0}</p>
                        </div>
                        <div className="glass-card p-4 text-center">
                            <p className="text-xs" style={{ color: "var(--text-muted)" }}>Duplicate Images</p>
                            <p className="text-2xl font-bold">{dupsData?.total_duplicates || 0}</p>
                        </div>
                        <div className="glass-card p-4 text-center">
                            <p className="text-xs" style={{ color: "var(--text-muted)" }}>Threshold</p>
                            <p className="text-2xl font-bold">0.98</p>
                        </div>
                    </div>

                    {/* Groups */}
                    <div className="space-y-4">
                        {(dupsData?.groups || []).map((group, idx) => (
                            <div key={group.group_id} className="glass-card p-5">
                                <div className="flex items-center justify-between mb-3">
                                    <h3 className="font-semibold flex items-center gap-2">
                                        <Copy size={16} style={{ color: "var(--warning)" }} />
                                        Group {idx + 1}
                                    </h3>
                                    <span className="badge badge-warning">{group.images.length} duplicates</span>
                                </div>
                                <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
                                    {group.images.map((img) => (
                                        <div
                                            key={img.id}
                                            onClick={() => openImageModal(img)}
                                            className="aspect-square rounded-lg overflow-hidden cursor-pointer transition-all hover:scale-105 hover:ring-2 hover:ring-[var(--warning)]"
                                            style={{ background: "var(--bg-secondary)" }}
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
                        ))}
                        {(dupsData?.groups || []).length === 0 && (
                            <div className="glass-card p-12 text-center">
                                <p className="text-lg font-semibold mb-1" style={{ color: "var(--success)" }}>No duplicates found!</p>
                                <p style={{ color: "var(--text-muted)" }}>This dataset has no near-duplicate images</p>
                            </div>
                        )}
                    </div>
                </>
            )}
        </div>
    );
}
