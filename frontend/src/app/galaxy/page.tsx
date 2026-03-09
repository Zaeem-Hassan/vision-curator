"use client";

import { Suspense, useRef, useMemo, useState, useCallback } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { OrbitControls, Html } from "@react-three/drei";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import { Orbit, Loader2 } from "lucide-react";
import * as THREE from "three";
import { api, type EmbeddingPoint, type Dataset } from "@/lib/api";
import { useAppStore } from "@/lib/store";

// Cluster colors palette
const CLUSTER_COLORS = [
    "#6366f1", "#ec4899", "#f59e0b", "#22c55e", "#3b82f6",
    "#a855f7", "#06b6d4", "#ef4444", "#84cc16", "#f97316",
    "#14b8a6", "#e879f9", "#64748b", "#fbbf24", "#38bdf8",
];

function getClusterColor(clusterId: number | null): string {
    if (clusterId === null || clusterId < 0) return "#4b5563";
    return CLUSTER_COLORS[clusterId % CLUSTER_COLORS.length];
}

export default function GalaxyPage() {
    return (
        <Suspense fallback={<LoadingState />}>
            <GalaxyContent />
        </Suspense>
    );
}

function GalaxyContent() {
    const searchParams = useSearchParams();
    const datasetIdParam = searchParams.get("dataset");
    const [selectedDatasetId, setSelectedDatasetId] = useState<string | null>(datasetIdParam);

    const { data: datasetsData } = useQuery({
        queryKey: ["datasets"],
        queryFn: () => api.listDatasets(0, 50),
    });

    const { data: embeddingData, isLoading } = useQuery({
        queryKey: ["embedding-map", selectedDatasetId],
        queryFn: () => api.getEmbeddingMap(selectedDatasetId!),
        enabled: !!selectedDatasetId,
    });

    const datasets = datasetsData?.datasets?.filter((d: Dataset) => d.status === "completed") || [];
    const points = embeddingData?.points || [];

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2">
                        <Orbit className="text-[var(--accent)]" /> Embedding Galaxy
                    </h1>
                    <p style={{ color: "var(--text-muted)" }}>
                        Interactive 3D visualization of image embeddings
                    </p>
                </div>
                <select
                    value={selectedDatasetId || ""}
                    onChange={(e) => setSelectedDatasetId(e.target.value || null)}
                    className="px-4 py-2 rounded-xl text-sm outline-none"
                    style={{ background: "var(--bg-card)", border: "1px solid var(--border)", color: "var(--text-primary)" }}
                >
                    <option value="">Select a dataset</option>
                    {datasets.map((ds: Dataset) => (
                        <option key={ds.id} value={ds.id}>{ds.name}</option>
                    ))}
                </select>
            </div>

            {!selectedDatasetId ? (
                <div className="glass-card p-16 text-center">
                    <Orbit size={48} className="mx-auto mb-4" style={{ color: "var(--text-muted)" }} />
                    <h3 className="text-xl font-semibold mb-2">Select a Dataset</h3>
                    <p style={{ color: "var(--text-muted)" }}>Choose a processed dataset to visualize its embedding galaxy</p>
                </div>
            ) : isLoading ? (
                <LoadingState />
            ) : points.length === 0 ? (
                <div className="glass-card p-16 text-center">
                    <p style={{ color: "var(--text-muted)" }}>No embedding data available. Process the dataset first.</p>
                </div>
            ) : (
                <div className="glass-card overflow-hidden" style={{ height: "calc(100vh - 200px)" }}>
                    <Canvas
                        camera={{ position: [0, 0, 50], fov: 60, near: 0.1, far: 1000 }}
                        style={{ background: "#0a0a0f" }}
                    >
                        <ambientLight intensity={0.5} />
                        <pointLight position={[10, 10, 10]} intensity={1} />
                        <PointCloud points={points} />
                        <OrbitControls
                            enableDamping
                            dampingFactor={0.1}
                            rotateSpeed={0.5}
                            zoomSpeed={0.8}
                            minDistance={5}
                            maxDistance={200}
                        />
                        <GridBackground />
                    </Canvas>

                    {/* Legend */}
                    <div
                        className="absolute bottom-4 left-4 p-3 rounded-xl text-xs space-y-1"
                        style={{ background: "rgba(10,10,15,0.9)", border: "1px solid var(--border)" }}
                    >
                        <p className="font-semibold mb-2">Legend</p>
                        <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full" style={{ background: "#ef4444" }}></div>
                            <span style={{ color: "var(--text-muted)" }}>Outlier</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full" style={{ background: "#f59e0b" }}></div>
                            <span style={{ color: "var(--text-muted)" }}>Duplicate</span>
                        </div>
                        <p className="pt-1" style={{ color: "var(--text-muted)" }}>Colors = Clusters</p>
                        <p style={{ color: "var(--text-muted)" }}>{points.length.toLocaleString()} points</p>
                    </div>
                </div>
            )}
        </div>
    );
}

function PointCloud({ points }: { points: EmbeddingPoint[] }) {
    const meshRef = useRef<THREE.InstancedMesh>(null!);
    const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);
    const { openImageModal } = useAppStore();

    const { positions, colors, scale } = useMemo(() => {
        const xs = points.map((p) => p.x);
        const ys = points.map((p) => p.y);
        const zs = points.map((p) => p.z);

        // Normalize to fit in view
        const maxRange = Math.max(
            Math.max(...xs) - Math.min(...xs),
            Math.max(...ys) - Math.min(...ys),
            Math.max(...zs) - Math.min(...zs)
        ) || 1;
        const sc = 40 / maxRange;

        const cx = (Math.max(...xs) + Math.min(...xs)) / 2;
        const cy = (Math.max(...ys) + Math.min(...ys)) / 2;
        const cz = (Math.max(...zs) + Math.min(...zs)) / 2;

        const pos = new Float32Array(points.length * 3);
        const col = new Float32Array(points.length * 3);

        points.forEach((p, i) => {
            pos[i * 3] = (p.x - cx) * sc;
            pos[i * 3 + 1] = (p.y - cy) * sc;
            pos[i * 3 + 2] = (p.z - cz) * sc;

            let color: THREE.Color;
            if (p.is_outlier) {
                color = new THREE.Color("#ef4444");
            } else if (p.is_duplicate) {
                color = new THREE.Color("#f59e0b");
            } else {
                color = new THREE.Color(getClusterColor(p.cluster_id));
            }
            col[i * 3] = color.r;
            col[i * 3 + 1] = color.g;
            col[i * 3 + 2] = color.b;
        });

        return { positions: pos, colors: col, scale: sc };
    }, [points]);

    const tempObject = useMemo(() => new THREE.Object3D(), []);

    useFrame(() => {
        if (!meshRef.current) return;
        points.forEach((_, i) => {
            tempObject.position.set(
                positions[i * 3],
                positions[i * 3 + 1],
                positions[i * 3 + 2]
            );
            const s = i === hoveredIdx ? 0.6 : 0.25;
            tempObject.scale.setScalar(s);
            tempObject.updateMatrix();
            meshRef.current.setMatrixAt(i, tempObject.matrix);
        });
        meshRef.current.instanceMatrix.needsUpdate = true;
    });

    // Color buffer
    const colorAttr = useMemo(() => {
        return new THREE.InstancedBufferAttribute(colors, 3);
    }, [colors]);

    return (
        <>
            <instancedMesh
                ref={meshRef}
                args={[undefined, undefined, points.length]}
                onPointerMove={(e) => {
                    if (e.instanceId !== undefined) setHoveredIdx(e.instanceId);
                }}
                onPointerOut={() => setHoveredIdx(null)}
                onClick={(e) => {
                    if (e.instanceId !== undefined) {
                        // Show image info
                    }
                }}
            >
                <sphereGeometry args={[1, 8, 8]}>
                    <instancedBufferAttribute attach="attributes-color" args={[colors, 3]} />
                </sphereGeometry>
                <meshBasicMaterial vertexColors toneMapped={false} />
            </instancedMesh>

            {/* Tooltip */}
            {hoveredIdx !== null && points[hoveredIdx] && (
                <Html
                    position={[
                        positions[hoveredIdx * 3],
                        positions[hoveredIdx * 3 + 1] + 1,
                        positions[hoveredIdx * 3 + 2],
                    ]}
                >
                    <div
                        className="px-3 py-2 rounded-lg text-xs whitespace-nowrap pointer-events-none"
                        style={{
                            background: "rgba(10,10,15,0.95)",
                            border: "1px solid var(--border)",
                            color: "var(--text-primary)",
                            transform: "translate(-50%, -100%)",
                        }}
                    >
                        <p className="font-semibold">{points[hoveredIdx].filename}</p>
                        <p style={{ color: "var(--text-muted)" }}>
                            Cluster: {points[hoveredIdx].cluster_id ?? "N/A"}
                            {points[hoveredIdx].is_outlier && " • Outlier"}
                            {points[hoveredIdx].is_duplicate && " • Duplicate"}
                        </p>
                    </div>
                </Html>
            )}
        </>
    );
}

function GridBackground() {
    return (
        <gridHelper args={[200, 40, "#1a1a2e", "#1a1a2e"]} rotation-x={Math.PI / 2} position={[0, 0, -25]} />
    );
}

function LoadingState() {
    return (
        <div className="glass-card p-16 text-center">
            <Loader2 size={32} className="mx-auto mb-4 animate-spin" style={{ color: "var(--accent)" }} />
            <p style={{ color: "var(--text-muted)" }}>Loading embedding data...</p>
        </div>
    );
}
