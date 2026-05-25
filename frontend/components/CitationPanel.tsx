"use client";

import { motion } from "framer-motion";
import { X, FileText, CheckCircle, AlertCircle } from "lucide-react";

interface Citation {
  chunk_id: string;
  title: string;
  authors: string[];
  year?: number;
  page_number?: number;
  snippet: string;
  is_verified: boolean;
}

interface CitationPanelProps {
  citations: Citation[];
  onClose: () => void;
}

export default function CitationPanel({ citations, onClose }: CitationPanelProps) {
  return (
    <motion.aside
      initial={{ x: "100%", opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: "100%", opacity: 0 }}
      transition={{ type: "spring", damping: 25, stiffness: 200 }}
      className="w-80 border-l border-surface-border bg-surface-card flex flex-col"
      aria-label="Citation sources"
      role="complementary"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-4 border-b border-surface-border">
        <div className="flex items-center gap-2">
          <FileText size={16} className="text-primary-400" />
          <h2 className="text-sm font-semibold text-slate-200">
            Sources ({citations.length})
          </h2>
        </div>
        <button
          onClick={onClose}
          aria-label="Close citation panel"
          className="w-7 h-7 rounded-md flex items-center justify-center
                     text-slate-400 hover:text-slate-200 hover:bg-surface
                     transition-colors focus:outline-none focus:ring-2
                     focus:ring-primary-500"
        >
          <X size={14} />
        </button>
      </div>

      {/* Citations list */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {citations.length === 0 ? (
          <p className="text-sm text-slate-500 text-center py-8">
            No citations for this response
          </p>
        ) : (
          citations.map((citation, index) => (
            <motion.div
              key={citation.chunk_id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="bg-surface border border-surface-border rounded-lg p-4 space-y-3"
            >
              {/* Citation header */}
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-slate-200 leading-tight line-clamp-2">
                    {citation.title}
                  </p>
                  {citation.authors.length > 0 && (
                    <p className="text-xs text-slate-400 mt-1">
                      {citation.authors.slice(0, 3).join(", ")}
                      {citation.authors.length > 3 ? " et al." : ""}
                      {citation.year ? ` (${citation.year})` : ""}
                    </p>
                  )}
                </div>
                <div
                  className={`flex-shrink-0 ${
                    citation.is_verified ? "text-green-400" : "text-yellow-400"
                  }`}
                  title={citation.is_verified ? "Verified citation" : "Unverified citation"}
                >
                  {citation.is_verified ? (
                    <CheckCircle size={14} />
                  ) : (
                    <AlertCircle size={14} />
                  )}
                </div>
              </div>

              {/* Page number */}
              {citation.page_number && (
                <div className="flex items-center gap-1">
                  <span className="text-xs bg-primary-900/50 text-primary-300 px-2 py-0.5 rounded">
                    Page {citation.page_number}
                  </span>
                </div>
              )}

              {/* Snippet */}
              <div className="bg-surface-card rounded-md p-3">
                <p className="text-xs text-slate-400 leading-relaxed line-clamp-4">
                  "{citation.snippet}"
                </p>
              </div>

              {/* Chunk ID */}
              <p className="text-xs text-slate-600 font-mono truncate">
                ID: {citation.chunk_id}
              </p>
            </motion.div>
          ))
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-surface-border">
        <p className="text-xs text-slate-500">
          {citations.filter((c) => c.is_verified).length} of {citations.length}{" "}
          citations verified
        </p>
      </div>
    </motion.aside>
  );
}
