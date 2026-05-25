"use client";

import { useState, useEffect, useCallback } from "react";
import { listDocuments, deleteDocument } from "@/utils/api";

export interface Document {
  id: string;
  title: string;
  authors: string[];
  publication_year?: number;
  status: "pending" | "processing" | "indexed" | "failed";
  page_count?: number;
  file_size_bytes?: number;
  created_at: string;
}

export function useDocuments() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  const fetchDocuments = useCallback(
    async (pageNum = 1, reset = false) => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await listDocuments(pageNum, 20);
        const docs: Document[] = data.data.documents;
        if (reset) {
          setDocuments(docs);
        } else {
          setDocuments((prev) => [...prev, ...docs]);
        }
        setHasMore(docs.length === 20);
        setPage(pageNum);
      } catch (err: any) {
        setError(err.message || "Failed to load documents");
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    fetchDocuments(1, true);
  }, [fetchDocuments]);

  const removeDocument = useCallback(async (documentId: string) => {
    try {
      await deleteDocument(documentId);
      setDocuments((prev) => prev.filter((d) => d.id !== documentId));
    } catch (err: any) {
      setError(err.message || "Failed to delete document");
    }
  }, []);

  const loadMore = useCallback(() => {
    if (!isLoading && hasMore) {
      fetchDocuments(page + 1);
    }
  }, [isLoading, hasMore, page, fetchDocuments]);

  const refresh = useCallback(() => {
    fetchDocuments(1, true);
  }, [fetchDocuments]);

  return {
    documents,
    isLoading,
    error,
    hasMore,
    removeDocument,
    loadMore,
    refresh,
  };
}
