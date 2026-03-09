"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Search, Upload, Loader2, Image as ImageIcon } from "lucide-react";
import { api, type ImageRecord, type Dataset } from "@/lib/api";
import { useAppStore } from "@/lib/store";

export default function SearchPage() {
    const [selectedDatasetId, setSelectedDatasetId] = useState<string | null>(null);
    const [queryFile, setQueryFile] = useState<File | null>(null);
    const [previewUrl, setPreviewUrl] = useState<string | null>(null);
    const { openImageModal } = useAppStore();

    const { data: datasetsData } = useQuery({
        queryKey: ["datasets"],
        queryFn: () => api.listDatasets(0, 50),
    });

    const searchMutation = useMutation({
        mutationFn: () => api.similaritySearch(selectedDatasetId!, queryFile!, 20),
    });

    const datasets = datasetsData?.datasets?.filter((d: Dataset) => d.status === "completed") || [];

    const handleFileSelect = (file: File) => {
        setQueryFile(file);
        setPreviewUrl(URL.createObjectURL(file));
    };

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold flex items-center gap-2">
                    <Search className="text-[var(--accent)]" /> Similarity Search
                </h1>
                <p style={{ color: "var(--text-muted)" }}>
                    Upload an image to find visually similar images in your datasets
                </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Query Panel */}
                <div className="glass-card p-6 space-y-4">
                    <h2 className="font-semibold text-lg">Query</h2>

                    <div>
                        <label className="block text-sm font-medium mb-1.5">Dataset</label>
                        <select
                            value={selectedDatasetId || ""}
                            onChange={(e) => setSelectedDatasetId(e.target.value || null)}
                            className="w-full px-4 py-2.5 rounded-xl text-sm outline-none"
                            style={{ background: "var(--bg-primary)", border: "1px solid var(--border)", color: "var(--text-primary)" }}
                        >
                            <option value="">Select dataset</option>
                            {datasets.map((ds: Dataset) => (
                                <option key={ds.id} value={ds.id}>{ds.name}</option>
                            ))}
                        </select>
                    </div>

                    {/* Upload area */}
                    <div
                        className="rounded-xl p-6 text-center cursor-pointer transition-all hover:border-[var(--accent)]"
                        style={{ border: "2px dashed var(--border)", background: "var(--bg-primary)" }}
                        onClick={() => document.getElementById("search-file")?.click()}
                    >
                        {previewUrl ? (
                            <img src={previewUrl} alt="Query" className="max-h-48 mx-auto rounded-lg" />
                        ) : (
                            <>
                                <Upload size={32} className="mx-auto mb-2" style={{ color: "var(--text-muted)" }} />
                                <p className="text-sm">Upload query image</p>
                            </>
                        )}
                        <input
                            id="search-file"
                            type="file"
                            accept="image/*"
                            className="hidden"
                            onChange={(e) => {
                                const f = e.target.files?.[0];
                                if (f) handleFileSelect(f);
                            }}
                        />
                    </div>

                    <button
                        onClick={() => searchMutation.mutate()}
                        disabled={!selectedDatasetId || !queryFile || searchMutation.isPending}
                        className="w-full py-3 rounded-xl font-semibold text-white text-sm transition-all disabled:opacity-40 hover:scale-[1.02]"
                        style={{ background: "var(--gradient-2)" }}
                    >
                        {searchMutation.isPending ? (
                            <span className="flex items-center justify-center gap-2"><Loader2 size={16} className="animate-spin" /> Searching...</span>
                        ) : (
                            "Search Similar Images"
                        )}
                    </button>
                </div>

                {/* Results */}
                <div className="lg:col-span-2">
                    <div className="glass-card p-6">
                        <h2 className="font-semibold text-lg mb-4">
                            Results
                            {searchMutation.data && (
                                <span className="text-sm font-normal ml-2" style={{ color: "var(--text-muted)" }}>
                                    ({searchMutation.data.results.length} matches)
                                </span>
                            )}
                        </h2>

                        {!searchMutation.data ? (
                            <div className="text-center py-16">
                                <ImageIcon size={48} className="mx-auto mb-4" style={{ color: "var(--text-muted)" }} />
                                <p style={{ color: "var(--text-muted)" }}>
                                    Upload a query image and select a dataset to search
                                </p>
                            </div>
                        ) : (
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                {searchMutation.data.results.map((img: ImageRecord, idx: number) => (
                                    <div
                                        key={img.id}
                                        onClick={() => openImageModal(img)}
                                        className="group cursor-pointer rounded-lg overflow-hidden transition-all hover:scale-105 hover:ring-2 hover:ring-[var(--accent)]"
                                        style={{ background: "var(--bg-secondary)" }}
                                    >
                                        <div className="aspect-square">
                                            <img
                                                src={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/uploads/${img.dataset_id}/${img.filename}`}
                                                alt={img.filename}
                                                className="w-full h-full object-cover"
                                                loading="lazy"
                                            />
                                        </div>
                                        <div className="p-2">
                                            <p className="text-xs truncate">{img.filename}</p>
                                            <p className="text-xs" style={{ color: "var(--accent)" }}>
                                                Dist: {searchMutation.data.distances[idx]?.toFixed(4)}
                                            </p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
