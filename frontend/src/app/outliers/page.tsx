"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, Loader2 } from "lucide-react";
import { api, type Dataset } from "@/lib/api";
import { useAppStore } from "@/lib/store";

export default function OutliersPage() {
    const [selectedDatasetId, setSelectedDatasetId] = useState<string | null>(null);
    const { openImageModal } = useAppStore();

    const { data: datasetsData } = useQuery({
        queryKey: ["datasets"],
        queryFn: () => api.listDatasets(0, 50),
    });

    const { data: outliersData, isLoading } = useQuery({
        queryKey: ["outliers", selectedDatasetId],
        queryFn: () => api.getDatasetOutliers(selectedDatasetId!),
        enabled: !!selectedDatasetId,
    });

    const datasets = datasetsData?.datasets?.filter((d: Dataset) => d.status === "completed") || [];
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2">
                        <AlertTriangle className="text-[var(--danger)]" /> Outlier Viewer
                    </h1>
                    <p style={{ color: "var(--text-muted)" }}>
                        Images flagged as anomalous by Isolation Forest &amp; k-NN analysis
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
                    <AlertTriangle size={48} className="mx-auto mb-4" style={{ color: "var(--text-muted)" }} />
                    <p style={{ color: "var(--text-muted)" }}>Select a processed dataset to view outliers</p>
                </div>
            ) : isLoading ? (
                <div className="glass-card p-16 text-center">
                    <Loader2 size={32} className="mx-auto mb-4 animate-spin" style={{ color: "var(--accent)" }} />
                </div>
            ) : (
                <>
                    <div className="glass-card p-4 flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <span className="text-sm" style={{ color: "var(--text-muted)" }}>Total outliers:</span>
                            <span className="font-bold text-lg" style={{ color: "var(--danger)" }}>
                                {outliersData?.total || 0}
                            </span>
                        </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3">
                        {(outliersData?.outliers || []).map((img) => (
                            <div
                                key={img.id}
                                onClick={() => openImageModal(img)}
                                className="group glass-card overflow-hidden cursor-pointer transition-all hover:translate-y-[-2px] hover:border-[var(--danger)]"
                            >
                                <div className="aspect-square">
                                    <img
                                        src={`${baseUrl}/uploads/${img.dataset_id}/${img.filename}`}
                                        alt={img.filename}
                                        className="w-full h-full object-cover"
                                        loading="lazy"
                                    />
                                </div>
                                <div className="p-3">
                                    <p className="text-xs truncate mb-1">{img.filename}</p>
                                    <div className="flex items-center justify-between">
                                        <span className="badge badge-danger text-[10px]">Outlier</span>
                                        <span className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>
                                            {img.outlier_score?.toFixed(3)}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>

                    {(outliersData?.outliers || []).length === 0 && (
                        <div className="glass-card p-12 text-center">
                            <p className="text-lg font-semibold mb-1" style={{ color: "var(--success)" }}>No outliers detected!</p>
                            <p style={{ color: "var(--text-muted)" }}>Dataset appears clean and consistent</p>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
