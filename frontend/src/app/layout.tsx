import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/lib/providers";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "VisionCurator — Dataset Intelligence Platform",
  description:
    "Self-supervised dataset intelligence and curation platform for computer vision. Analyze, cluster, and explore image datasets with AI.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} font-sans antialiased`}>
        <Providers>
          <ClientLayout>{children}</ClientLayout>
        </Providers>
      </body>
    </html>
  );
}

// Separate client component for sidebar + modal
import { ClientLayout } from "@/components/ClientLayout";
