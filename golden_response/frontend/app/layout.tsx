import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "RAG Research Assistant",
  description: "AI-powered academic research assistant with semantic search and citation-aware responses",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-surface text-slate-100 min-h-screen`}>
        {children}
      </body>
    </html>
  );
}
