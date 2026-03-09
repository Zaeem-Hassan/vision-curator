"use client";

import { Sidebar } from "@/components/Sidebar";
import { ImageModal } from "@/components/ImageModal";
import { useAppStore } from "@/lib/store";

export function ClientLayout({ children }: { children: React.ReactNode }) {
    const { isSidebarCollapsed } = useAppStore();

    return (
        <>
            <Sidebar />
            <main
                className="min-h-screen transition-all duration-300"
                style={{
                    marginLeft: isSidebarCollapsed ? "72px" : "260px",
                    padding: "24px 32px",
                }}
            >
                {children}
            </main>
            <ImageModal />
        </>
    );
}
