"use client";

import { useState, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
    Upload,
    Database,
    Loader2,
    CheckCircle2,
    XCircle,
    Clock,
    Play,
    Trash2,
    X,
} from "lucide-react";
import Link from "next/link";
import { api, type Dataset } from "@/lib/api";

export default function DatasetsPage() {
    const [showUpload, setShowUpload] = useState(false);
    const queryClient = useQueryClient();

    const { data, isLoading } = useQuery({
        queryKey: ["datasets"],
        queryFn: () => api.listDatasets(0, 50),
        // Auto-poll every 3s while any dataset is processing
        refetchInterval: (query) => {
            const ds = query.state.data?.datasets ?? [];
            return ds.some((d: Dataset) => d.status === "processing") ? 3000 : false;
        },
    });

    const deleteMutation = useMutation({
        mutationFn: (id: string) => api.deleteDataset(id),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ["datasets"] }),
    });

    const processMutation = useMutation({
        mutationFn: (id: string) => api.processDataset(id),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ["datasets"] }),
    });

    const datasets = data?.datasets || [];

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold">Datasets</h1>
                    <p style={{ color: "var(--text-muted)" }}>
                        Manage and analyze your image datasets
                    </p>
                </div>
                <button
                    onClick={() => setShowUpload(true)}
                    className="flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-white text-sm transition-transform hover:scale-105"
                    style={{ background: "var(--gradient-1)" }}
                >
                    <Upload size={16} />
                    Upload Dataset
                </button>
            </div>

            {isLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {[...Array(6)].map((_, i) => (
                        <div key={i} className="glass-card p-5 h-48 shimmer" />
                    ))}
                </div>
            ) : datasets.length === 0 ? (
                <div className="glass-card p-16 text-center">
                    <Database size={48} className="mx-auto mb-4" style={{ color: "var(--text-muted)" }} />
                    <h3 className="text-xl font-semibold mb-2">No datasets yet</h3>
                    <p style={{ color: "var(--text-muted)" }}>
                        Upload your first image dataset to get started
                    </p>
                    <button
                        onClick={() => setShowUpload(true)}
                        className="mt-4 px-5 py-2.5 rounded-xl font-semibold text-white text-sm"
                        style={{ background: "var(--gradient-1)" }}
                    >
                        Upload Dataset
                    </button>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {datasets.map((ds) => (
                        <DatasetCard
                            key={ds.id}
                            dataset={ds}
                            onProcess={() => processMutation.mutate(ds.id)}
                            onDelete={() => {
                                if (confirm("Delete this dataset?")) deleteMutation.mutate(ds.id);
                            }}
                        />
                    ))}
                </div>
            )}

            {showUpload && (
                <UploadDialog
                    onClose={() => setShowUpload(false)}
                    onSuccess={() => {
                        setShowUpload(false);
                        queryClient.invalidateQueries({ queryKey: ["datasets"] });
                    }}
                />
            )}
        </div>
    );
}

function DatasetCard({
    dataset,
    onProcess,
    onDelete,
}: {
    dataset: Dataset;
    onProcess: () => void;
    onDelete: () => void;
}) {
    const statusConfig: Record<string, { icon: typeof Clock; badge: string; color: string }> = {
        pending: { icon: Clock, badge: "badge-info", color: "var(--info)" },
        processing: { icon: Loader2, badge: "badge-processing", color: "var(--accent)" },
        completed: { icon: CheckCircle2, badge: "badge-success", color: "var(--success)" },
        failed: { icon: XCircle, badge: "badge-danger", color: "var(--danger)" },
    };

    const sc = statusConfig[dataset.status] || statusConfig.pending;
    const StatusIcon = sc.icon;

    return (
        <div className="glass-card p-5 transition-all duration-300 hover:translate-y-[-2px] flex flex-col">
            <div className="flex items-start justify-between mb-3">
                <Link href={`/datasets/${dataset.id}`} className="flex-1 min-w-0">
                    <h3 className="font-semibold text-lg truncate hover:text-[var(--accent)] transition-colors">
                        {dataset.name}
                    </h3>
                </Link>
                <span className={`badge ${sc.badge} flex items-center gap-1`}>
                    <StatusIcon size={12} className={dataset.status === "processing" ? "animate-spin" : ""} />
                    {dataset.status}
                </span>
            </div>

            {dataset.description && (
                <p className="text-sm mb-3 line-clamp-2" style={{ color: "var(--text-muted)" }}>
                    {dataset.description}
                </p>
            )}

            <div className="grid grid-cols-2 gap-3 text-sm flex-1">
                <Stat label="Images" value={dataset.image_count.toLocaleString()} />
                <Stat label="Clusters" value={dataset.cluster_count.toString()} />
                <Stat label="Duplicates" value={`${dataset.duplicate_percentage.toFixed(1)}%`} />
                <Stat label="Outliers" value={dataset.outlier_count.toString()} />
            </div>

            <div className="flex gap-2 mt-4 pt-3" style={{ borderTop: "1px solid var(--border)" }}>
                {(dataset.status === "pending" || dataset.status === "failed") && (
                    <button
                        onClick={onProcess}
                        className="flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-medium text-white transition-colors"
                        style={{ background: dataset.status === "failed" ? "var(--danger)" : "var(--accent)" }}
                    >
                        <Play size={14} /> {dataset.status === "failed" ? "Retry" : "Process"}
                    </button>
                )}
                {dataset.status === "processing" && (
                    <div className="flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-medium" style={{ color: "var(--accent)" }}>
                        <Loader2 size={14} className="animate-spin" /> Processing…
                    </div>
                )}
                {dataset.status === "completed" && (
                    <Link
                        href={`/datasets/${dataset.id}`}
                        className="flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-medium text-white transition-colors"
                        style={{ background: "var(--accent)" }}
                    >
                        Explore
                    </Link>
                )}
                <button
                    onClick={onDelete}
                    className="p-2 rounded-lg transition-colors hover:bg-red-500/20"
                    style={{ color: "var(--danger)" }}
                >
                    <Trash2 size={16} />
                </button>
            </div>
        </div>
    );
}

function Stat({ label, value }: { label: string; value: string }) {
    return (
        <div>
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>{label}</p>
            <p className="font-semibold">{value}</p>
        </div>
    );
}

function UploadDialog({ onClose, onSuccess }: { onClose: () => void; onSuccess: () => void }) {
    const [name, setName] = useState("");
    const [description, setDescription] = useState("");
    const [files, setFiles] = useState<File[]>([]);
    const [isDragging, setIsDragging] = useState(false);

    const uploadMutation = useMutation({
        mutationFn: () => api.uploadDataset(name, description, files),
        onSuccess,
    });

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        const droppedFiles = Array.from(e.dataTransfer.files).filter((f) =>
            f.type.startsWith("image/")
        );
        setFiles((prev) => [...prev, ...droppedFiles]);
    }, []);

    return (
        <div
            className="fixed inset-0 z-[80] flex items-center justify-center p-8"
            style={{ background: "rgba(0,0,0,0.7)", backdropFilter: "blur(4px)" }}
            onClick={onClose}
        >
            <div className="glass-card w-full max-w-lg p-6 space-y-5" onClick={(e) => e.stopPropagation()}>
                <div className="flex items-center justify-between">
                    <h2 className="text-xl font-bold">Upload Dataset</h2>
                    <button onClick={onClose} className="p-1 rounded-lg hover:bg-[var(--bg-hover)]">
                        <X size={20} />
                    </button>
                </div>

                <div>
                    <label className="block text-sm font-medium mb-1.5">Dataset Name</label>
                    <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="My Image Dataset"
                        className="w-full px-4 py-2.5 rounded-xl text-sm outline-none transition-colors"
                        style={{ background: "var(--bg-primary)", border: "1px solid var(--border)", color: "var(--text-primary)" }}
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium mb-1.5">Description (optional)</label>
                    <textarea
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        placeholder="Describe your dataset..."
                        rows={2}
                        className="w-full px-4 py-2.5 rounded-xl text-sm outline-none resize-none transition-colors"
                        style={{ background: "var(--bg-primary)", border: "1px solid var(--border)", color: "var(--text-primary)" }}
                    />
                </div>

                {/* Upload mode buttons */}
                <div className="flex gap-2">
                    <button
                        type="button"
                        onClick={() => document.getElementById("file-input")?.click()}
                        className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-medium transition-colors"
                        style={{ background: "var(--bg-primary)", border: "1px solid var(--border)", color: "var(--text-secondary)" }}
                    >
                        <Upload size={15} /> Select Images
                    </button>
                    <button
                        type="button"
                        onClick={() => document.getElementById("folder-input")?.click()}
                        className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-medium transition-colors"
                        style={{ background: "var(--bg-primary)", border: "1px solid var(--border)", color: "var(--text-secondary)" }}
                    >
                        <Database size={15} /> Select Folder
                    </button>
                </div>

                {/* Drop Zone */}
                <div
                    onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                    onDragLeave={() => setIsDragging(false)}
                    onDrop={handleDrop}
                    className={`rounded-xl p-6 text-center transition-all ${isDragging ? "scale-[1.02]" : ""}`}
                    style={{
                        border: `2px dashed ${isDragging ? "var(--accent)" : "var(--border)"}`,
                        background: isDragging ? "var(--accent-glow)" : "var(--bg-primary)",
                    }}
                >
                    <Upload size={24} className="mx-auto mb-1" style={{ color: "var(--text-muted)" }} />
                    <p className="text-sm" style={{ color: "var(--text-muted)" }}>or drag &amp; drop images here</p>

                    {/* Hidden inputs */}
                    <input
                        id="file-input"
                        type="file"
                        multiple
                        accept="image/*"
                        className="hidden"
                        onChange={(e) => {
                            const selected = Array.from(e.target.files || []).filter(f => f.type.startsWith("image/"));
                            setFiles((prev) => [...prev, ...selected]);
                            e.target.value = "";
                        }}
                    />
                    <input
                        id="folder-input"
                        type="file"
                        // @ts-expect-error — webkitdirectory is non-standard but supported by all modern browsers
                        webkitdirectory=""
                        multiple
                        className="hidden"
                        onChange={(e) => {
                            const selected = Array.from(e.target.files || []).filter(f => f.type.startsWith("image/"));
                            setFiles((prev) => [...prev, ...selected]);
                            e.target.value = "";
                        }}
                    />
                </div>

                {files.length > 0 && (
                    <div className="flex items-center justify-between text-sm">
                        <span style={{ color: "var(--text-secondary)" }}>
                            {files.length} images selected ({(files.reduce((a, f) => a + f.size, 0) / 1024 / 1024).toFixed(1)} MB)
                        </span>
                        <button
                            type="button"
                            onClick={() => setFiles([])}
                            className="text-xs px-2 py-1 rounded-lg hover:bg-red-500/20"
                            style={{ color: "var(--danger)" }}
                        >
                            Clear
                        </button>
                    </div>
                )}

                <button
                    onClick={() => uploadMutation.mutate()}
                    disabled={!name || files.length === 0 || uploadMutation.isPending}
                    className="w-full py-3 rounded-xl font-semibold text-white text-sm transition-all disabled:opacity-40 disabled:cursor-not-allowed hover:scale-[1.02]"
                    style={{ background: "var(--gradient-1)" }}
                >
                    {uploadMutation.isPending ? (
                        <span className="flex items-center justify-center gap-2"><Loader2 size={16} className="animate-spin" /> Uploading...</span>
                    ) : (
                        `Upload ${files.length} Images`
                    )}
                </button>
            </div>
        </div>
    );
}
