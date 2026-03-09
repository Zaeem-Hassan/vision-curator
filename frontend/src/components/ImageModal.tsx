"use client";

import { X } from "lucide-react";
import { useAppStore } from "@/lib/store";

export function ImageModal() {
    const { selectedImage, isImageModalOpen, closeImageModal } = useAppStore();

    if (!isImageModalOpen || !selectedImage) return null;

    const imageUrl = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/uploads/${selectedImage.dataset_id}/${selectedImage.filename}`;

    return (
        <div
            className="fixed inset-0 z-[100] flex items-center justify-center p-8"
            style={{ background: "rgba(0, 0, 0, 0.85)", backdropFilter: "blur(8px)" }}
            onClick={closeImageModal}
        >
            <div
                className="relative max-w-5xl w-full glass-card overflow-hidden"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Close button */}
                <button
                    onClick={closeImageModal}
                    className="absolute top-4 right-4 z-10 w-10 h-10 rounded-full flex items-center justify-center transition-colors"
                    style={{ background: "rgba(0,0,0,0.5)" }}
                >
                    <X size={20} />
                </button>

                <div className="flex flex-col md:flex-row">
                    {/* Image */}
                    <div className="flex-1 flex items-center justify-center p-6" style={{ background: "var(--bg-primary)" }}>
                        <img
                            src={imageUrl}
                            alt={selectedImage.filename}
                            className="max-h-[70vh] object-contain rounded-lg"
                        />
                    </div>

                    {/* Info Panel */}
                    <div className="w-full md:w-80 p-6 space-y-4" style={{ borderLeft: "1px solid var(--border)" }}>
                        <h3 className="text-lg font-semibold truncate">{selectedImage.filename}</h3>

                        <div className="space-y-3 text-sm">
                            <InfoRow label="Dimensions" value={selectedImage.width && selectedImage.height ? `${selectedImage.width} × ${selectedImage.height}` : "N/A"} />
                            <InfoRow label="File Size" value={formatBytes(selectedImage.file_size)} />
                            <InfoRow label="Cluster" value={selectedImage.cluster_id !== null ? `#${selectedImage.cluster_id}` : "N/A"} />
                            <InfoRow label="Outlier Score" value={selectedImage.outlier_score?.toFixed(4) ?? "N/A"} />

                            <div className="flex gap-2 pt-2">
                                {selectedImage.is_duplicate && <span className="badge badge-warning">Duplicate</span>}
                                {selectedImage.is_outlier && <span className="badge badge-danger">Outlier</span>}
                                {!selectedImage.is_duplicate && !selectedImage.is_outlier && <span className="badge badge-success">Clean</span>}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

function InfoRow({ label, value }: { label: string; value: string }) {
    return (
        <div className="flex justify-between">
            <span style={{ color: "var(--text-muted)" }}>{label}</span>
            <span className="font-mono">{value}</span>
        </div>
    );
}

function formatBytes(bytes: number): string {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}
