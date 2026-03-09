"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Database,
  Image as ImageIcon,
  Copy,
  AlertTriangle,
  Boxes,
  Loader2,
  TrendingUp,
  Sparkles,
} from "lucide-react";
import Link from "next/link";
import { api, type DashboardStats } from "@/lib/api";

const defaultStats: DashboardStats = {
  total_datasets: 0,
  total_images: 0,
  total_duplicates: 0,
  total_outliers: 0,
  total_clusters: 0,
  processing_datasets: 0,
  completed_datasets: 0,
  storage_used_mb: 0,
};

export default function DashboardPage() {
  const { data: stats = defaultStats, isLoading } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: api.getDashboardStats,
  });

  const statCards = [
    {
      label: "Total Datasets",
      value: stats.total_datasets,
      icon: Database,
      gradient: "linear-gradient(135deg, #6366f1, #a855f7)",
      href: "/datasets",
    },
    {
      label: "Total Images",
      value: stats.total_images.toLocaleString(),
      icon: ImageIcon,
      gradient: "linear-gradient(135deg, #3b82f6, #06b6d4)",
      href: "/datasets",
    },
    {
      label: "Duplicates Found",
      value: stats.total_duplicates.toLocaleString(),
      icon: Copy,
      gradient: "linear-gradient(135deg, #f59e0b, #ef4444)",
      href: "/duplicates",
    },
    {
      label: "Outliers Flagged",
      value: stats.total_outliers.toLocaleString(),
      icon: AlertTriangle,
      gradient: "linear-gradient(135deg, #ef4444, #ec4899)",
      href: "/outliers",
    },
    {
      label: "Clusters",
      value: stats.total_clusters,
      icon: Boxes,
      gradient: "linear-gradient(135deg, #22c55e, #06b6d4)",
      href: "/clusters",
    },
    {
      label: "Processing",
      value: stats.processing_datasets,
      icon: Loader2,
      gradient: "linear-gradient(135deg, #a855f7, #ec4899)",
      href: "/datasets",
    },
  ];

  return (
    <div className="space-y-8">
      {/* Hero */}
      <div className="relative overflow-hidden rounded-2xl p-8" style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)" }}>
        <div className="absolute inset-0 opacity-10" style={{ background: "var(--gradient-1)" }} />
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-2">
            <Sparkles className="text-[var(--accent)]" size={28} />
            <h1 className="text-3xl font-bold gradient-text">VisionCurator</h1>
          </div>
          <p className="text-lg" style={{ color: "var(--text-secondary)" }}>
            Self-Supervised Dataset Intelligence Platform
          </p>
          <p className="mt-2 max-w-2xl" style={{ color: "var(--text-muted)" }}>
            Upload image datasets, compute embeddings with DINOv2, detect duplicates &amp; outliers,
            cluster semantically, and explore your data in an interactive 3D galaxy.
          </p>
          <div className="mt-6 flex gap-3">
            <Link
              href="/datasets"
              className="px-5 py-2.5 rounded-xl font-semibold text-white text-sm transition-transform hover:scale-105"
              style={{ background: "var(--gradient-1)" }}
            >
              Upload Dataset
            </Link>
            <Link
              href="/galaxy"
              className="px-5 py-2.5 rounded-xl font-semibold text-sm transition-colors"
              style={{ background: "var(--bg-hover)", border: "1px solid var(--border)", color: "var(--text-secondary)" }}
            >
              Explore Galaxy
            </Link>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {statCards.map((card) => (
          <Link key={card.label} href={card.href}>
            <div className="glass-card p-5 transition-all duration-300 cursor-pointer group hover:translate-y-[-2px]">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm mb-1" style={{ color: "var(--text-muted)" }}>
                    {card.label}
                  </p>
                  <p className="text-3xl font-bold">
                    {isLoading ? (
                      <span className="inline-block w-16 h-8 rounded shimmer" />
                    ) : (
                      card.value
                    )}
                  </p>
                </div>
                <div
                  className="w-11 h-11 rounded-xl flex items-center justify-center opacity-80 group-hover:opacity-100 transition-opacity"
                  style={{ background: card.gradient }}
                >
                  <card.icon size={20} className="text-white" />
                </div>
              </div>
              <div className="mt-3 flex items-center gap-1 text-xs" style={{ color: "var(--text-muted)" }}>
                <TrendingUp size={12} />
                <span>View details →</span>
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="glass-card p-6">
        <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <QuickAction
            title="Upload & Analyze"
            desc="Upload a new image dataset for automated analysis"
            href="/datasets"
            gradient="var(--gradient-1)"
          />
          <QuickAction
            title="Search Similar"
            desc="Find visually similar images across your datasets"
            href="/search"
            gradient="var(--gradient-2)"
          />
          <QuickAction
            title="Explore Embeddings"
            desc="Visualize your dataset in 3D embedding space"
            href="/galaxy"
            gradient="var(--gradient-3)"
          />
        </div>
      </div>
    </div>
  );
}

function QuickAction({ title, desc, href, gradient }: { title: string; desc: string; href: string; gradient: string }) {
  return (
    <Link href={href}>
      <div
        className="p-4 rounded-xl transition-all duration-300 cursor-pointer hover:translate-y-[-2px]"
        style={{ background: "var(--bg-hover)", border: "1px solid var(--border)" }}
      >
        <div className="w-2 h-2 rounded-full mb-3" style={{ background: gradient }} />
        <h3 className="font-semibold mb-1">{title}</h3>
        <p className="text-sm" style={{ color: "var(--text-muted)" }}>{desc}</p>
      </div>
    </Link>
  );
}
