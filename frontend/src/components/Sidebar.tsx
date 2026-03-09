"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
    LayoutDashboard,
    Database,
    Orbit,
    Search,
    Copy,
    AlertTriangle,
    Boxes,
    ChevronLeft,
    ChevronRight,
    Sparkles,
} from "lucide-react";
import { useAppStore } from "@/lib/store";

const navItems = [
    { href: "/", icon: LayoutDashboard, label: "Dashboard" },
    { href: "/datasets", icon: Database, label: "Datasets" },
    { href: "/galaxy", icon: Orbit, label: "Embedding Galaxy" },
    { href: "/search", icon: Search, label: "Similarity Search" },
    { href: "/duplicates", icon: Copy, label: "Duplicates" },
    { href: "/outliers", icon: AlertTriangle, label: "Outliers" },
    { href: "/clusters", icon: Boxes, label: "Cluster Explorer" },
];

export function Sidebar() {
    const pathname = usePathname();
    const { isSidebarCollapsed, toggleSidebar } = useAppStore();

    return (
        <aside
            className={`fixed left-0 top-0 h-screen z-50 flex flex-col transition-all duration-300 ease-in-out ${isSidebarCollapsed ? "w-[72px]" : "w-[260px]"
                }`}
            style={{
                background: "rgba(10, 10, 15, 0.95)",
                borderRight: "1px solid var(--border)",
                backdropFilter: "blur(20px)",
            }}
        >
            {/* Logo */}
            <div className="flex items-center gap-3 px-5 h-16 flex-shrink-0">
                <div
                    className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
                    style={{ background: "var(--gradient-1)" }}
                >
                    <Sparkles size={20} className="text-white" />
                </div>
                {!isSidebarCollapsed && (
                    <div className="overflow-hidden">
                        <h1 className="text-lg font-bold gradient-text whitespace-nowrap">
                            VisionCurator
                        </h1>
                        <p className="text-[10px] tracking-widest uppercase" style={{ color: "var(--text-muted)" }}>
                            Dataset Intelligence
                        </p>
                    </div>
                )}
            </div>

            {/* Divider */}
            <div className="mx-4 h-px" style={{ background: "var(--border)" }} />

            {/* Navigation */}
            <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
                {navItems.map((item) => {
                    const isActive =
                        pathname === item.href ||
                        (item.href !== "/" && pathname.startsWith(item.href));

                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group relative ${isActive
                                    ? "text-white"
                                    : "hover:bg-[var(--bg-hover)]"
                                }`}
                            style={{
                                color: isActive ? "var(--text-primary)" : "var(--text-secondary)",
                                background: isActive ? "var(--bg-hover)" : undefined,
                            }}
                        >
                            {isActive && (
                                <div
                                    className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 rounded-r-full"
                                    style={{ background: "var(--gradient-1)" }}
                                />
                            )}
                            <item.icon
                                size={20}
                                className="flex-shrink-0"
                                style={{
                                    color: isActive ? "var(--accent)" : undefined,
                                }}
                            />
                            {!isSidebarCollapsed && (
                                <span className="text-sm font-medium whitespace-nowrap">
                                    {item.label}
                                </span>
                            )}
                        </Link>
                    );
                })}
            </nav>

            {/* Collapse Toggle */}
            <button
                onClick={toggleSidebar}
                className="flex items-center justify-center h-12 transition-colors hover:bg-[var(--bg-hover)]"
                style={{ borderTop: "1px solid var(--border)" }}
            >
                {isSidebarCollapsed ? (
                    <ChevronRight size={18} style={{ color: "var(--text-muted)" }} />
                ) : (
                    <ChevronLeft size={18} style={{ color: "var(--text-muted)" }} />
                )}
            </button>
        </aside>
    );
}
