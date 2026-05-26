"use client";

import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import {
  Upload, FileText, CheckCircle, XCircle,
  Loader2, AlertCircle, Trash2
} from "lucide-react";
import { uploadDocument } from "@/utils/api";

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  status: "uploading" | "processing" | "indexed" | "failed";
  progress: number;
  documentId?: string;
  error?: string;
}

export default function DocumentUpload() {
  const [files, setFiles] = useState<UploadedFile[]>([]);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    for (const file of acceptedFiles) {
      const fileId = `${Date.now()}-${file.name}`;

      // Add to list with uploading status
      setFiles((prev) => [
        ...prev,
        {
          id: fileId,
          name: file.name,
          size: file.size,
          status: "uploading",
          progress: 0,
        },
      ]);

      try {
        // Simulate progress
        setFiles((prev) =>
          prev.map((f) => (f.id === fileId ? { ...f, progress: 30 } : f))
        );

        const result = await uploadDocument(file);

        setFiles((prev) =>
          prev.map((f) =>
            f.id === fileId
              ? {
                  ...f,
                  status: "processing",
                  progress: 70,
                  documentId: result.data.document_id,
                }
              : f
          )
        );

        // Poll for completion (simplified)
        setTimeout(() => {
          setFiles((prev) =>
            prev.map((f) =>
              f.id === fileId ? { ...f, status: "indexed", progress: 100 } : f
            )
          );
        }, 3000);
      } catch (error: any) {
        setFiles((prev) =>
          prev.map((f) =>
            f.id === fileId
              ? {
                  ...f,
                  status: "failed",
                  progress: 0,
                  error: error.message || "Upload failed",
                }
              : f
          )
        );
      }
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
    maxSize: 50 * 1024 * 1024, // 50MB
    multiple: true,
  });

  const removeFile = (fileId: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== fileId));
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const statusConfig = {
    uploading: { icon: <Loader2 size={14} className="animate-spin" />, color: "text-blue-400", label: "Uploading..." },
    processing: { icon: <Loader2 size={14} className="animate-spin" />, color: "text-yellow-400", label: "Processing..." },
    indexed: { icon: <CheckCircle size={14} />, color: "text-green-400", label: "Indexed" },
    failed: { icon: <XCircle size={14} />, color: "text-red-400", label: "Failed" },
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-100 mb-1">
          Upload Research Papers
        </h2>
        <p className="text-sm text-slate-400">
          Upload PDF files to index them for semantic search and Q&A.
          Maximum file size: 50MB per file.
        </p>
      </div>

      {/* Drop zone */}
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-xl p-10 text-center cursor-pointer
          transition-all duration-200 focus:outline-none focus:ring-2
          focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-surface
          ${
            isDragActive
              ? "border-primary-500 bg-primary-500/5 drop-zone-active"
              : "border-surface-border hover:border-primary-500/50 hover:bg-surface-card"
          }
        `}
        role="button"
        aria-label="Upload PDF files by clicking or dragging"
        tabIndex={0}
      >
        <input {...getInputProps()} aria-label="File input" />
        <motion.div
          animate={{ scale: isDragActive ? 1.05 : 1 }}
          transition={{ duration: 0.2 }}
          className="flex flex-col items-center gap-4"
        >
          <div
            className={`w-16 h-16 rounded-2xl flex items-center justify-center
                        ${isDragActive ? "bg-primary-600" : "bg-surface-card"}`}
          >
            <Upload
              size={28}
              className={isDragActive ? "text-white" : "text-slate-400"}
            />
          </div>
          <div>
            <p className="text-slate-200 font-medium">
              {isDragActive
                ? "Drop your PDFs here"
                : "Drag & drop PDFs here"}
            </p>
            <p className="text-slate-400 text-sm mt-1">
              or{" "}
              <span className="text-primary-400 underline">
                click to browse
              </span>
            </p>
          </div>
          <p className="text-xs text-slate-500">
            PDF files only • Max 50MB per file
          </p>
        </motion.div>
      </div>

      {/* File list */}
      <AnimatePresence>
        {files.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-3"
          >
            <h3 className="text-sm font-medium text-slate-300">
              Uploaded Files ({files.length})
            </h3>
            {files.map((file) => {
              const status = statusConfig[file.status];
              return (
                <motion.div
                  key={file.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 10 }}
                  className="bg-surface-card border border-surface-border rounded-lg p-4"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-red-900/30 rounded-lg flex items-center justify-center flex-shrink-0">
                      <FileText size={18} className="text-red-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-200 truncate">
                        {file.name}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className={`flex items-center gap-1 text-xs ${status.color}`}>
                          {status.icon}
                          {status.label}
                        </span>
                        <span className="text-xs text-slate-500">
                          {formatSize(file.size)}
                        </span>
                      </div>
                      {file.error && (
                        <p className="text-xs text-red-400 mt-1 flex items-center gap-1">
                          <AlertCircle size={10} />
                          {file.error}
                        </p>
                      )}
                    </div>
                    <button
                      onClick={() => removeFile(file.id)}
                      aria-label={`Remove ${file.name}`}
                      className="w-7 h-7 rounded-md flex items-center justify-center
                                 text-slate-500 hover:text-red-400 hover:bg-red-900/20
                                 transition-colors focus:outline-none focus:ring-2
                                 focus:ring-red-500"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>

                  {/* Progress bar */}
                  {(file.status === "uploading" || file.status === "processing") && (
                    <div className="mt-3">
                      <div className="h-1 bg-surface rounded-full overflow-hidden">
                        <motion.div
                          className="h-full bg-primary-500 rounded-full"
                          initial={{ width: 0 }}
                          animate={{ width: `${file.progress}%` }}
                          transition={{ duration: 0.5 }}
                        />
                      </div>
                    </div>
                  )}
                </motion.div>
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
