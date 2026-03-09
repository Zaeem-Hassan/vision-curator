/**
 * Global state management using Zustand.
 */
import { create } from "zustand";
import type { Dataset, ImageRecord } from "./api";

interface AppState {
    // Selected dataset
    selectedDataset: Dataset | null;
    setSelectedDataset: (dataset: Dataset | null) => void;

    // Image modal
    selectedImage: ImageRecord | null;
    isImageModalOpen: boolean;
    openImageModal: (image: ImageRecord) => void;
    closeImageModal: () => void;

    // Sidebar
    isSidebarCollapsed: boolean;
    toggleSidebar: () => void;

    // Galaxy hover
    hoveredPointId: string | null;
    setHoveredPointId: (id: string | null) => void;

    // Filters
    activeClusterFilter: number | null;
    setActiveClusterFilter: (clusterId: number | null) => void;
    showDuplicatesOnly: boolean;
    setShowDuplicatesOnly: (show: boolean) => void;
    showOutliersOnly: boolean;
    setShowOutliersOnly: (show: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
    selectedDataset: null,
    setSelectedDataset: (dataset) => set({ selectedDataset: dataset }),

    selectedImage: null,
    isImageModalOpen: false,
    openImageModal: (image) =>
        set({ selectedImage: image, isImageModalOpen: true }),
    closeImageModal: () => set({ selectedImage: null, isImageModalOpen: false }),

    isSidebarCollapsed: false,
    toggleSidebar: () =>
        set((s) => ({ isSidebarCollapsed: !s.isSidebarCollapsed })),

    hoveredPointId: null,
    setHoveredPointId: (id) => set({ hoveredPointId: id }),

    activeClusterFilter: null,
    setActiveClusterFilter: (clusterId) =>
        set({ activeClusterFilter: clusterId }),
    showDuplicatesOnly: false,
    setShowDuplicatesOnly: (show) => set({ showDuplicatesOnly: show }),
    showOutliersOnly: false,
    setShowOutliersOnly: (show) => set({ showOutliersOnly: show }),
}));
