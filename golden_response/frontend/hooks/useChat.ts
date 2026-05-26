"use client";

import { useState, useCallback, useRef } from "react";
import { v4 as uuidv4 } from "uuid";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  confidence?: number;
  isStreaming?: boolean;
  error?: string;
}

interface Citation {
  chunk_id: string;
  title: string;
  authors: string[];
  year?: number;
  page_number?: number;
  snippet: string;
  is_verified: boolean;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const getAuthToken = (): string => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("access_token") || "";
    }
    return "";
  };

  const sendMessage = useCallback(async (query: string) => {
    if (!query.trim() || isLoading) return;

    setError(null);
    setIsLoading(true);

    // Add user message
    const userMessageId = uuidv4();
    setMessages((prev) => [
      ...prev,
      { id: userMessageId, role: "user", content: query },
    ]);

    // Add placeholder assistant message
    const assistantMessageId = uuidv4();
    setMessages((prev) => [
      ...prev,
      {
        id: assistantMessageId,
        role: "assistant",
        content: "",
        isStreaming: true,
      },
    ]);

    // Create abort controller for this request
    abortControllerRef.current = new AbortController();

    try {
      const token = getAuthToken();
      const response = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          query,
          session_id: sessionId,
          stream: true,
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }

      // Extract session ID from response headers
      const newSessionId = response.headers.get("X-Session-ID");
      if (newSessionId) {
        setSessionId(newSessionId);
      }

      // Parse SSE stream
      const reader = response.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let buffer = "";
      let fullContent = "";
      let finalCitations: Citation[] = [];
      let finalConfidence: number | undefined;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const dataStr = line.slice(6).trim();
            if (!dataStr || dataStr === "{}") continue;

            try {
              const data = JSON.parse(dataStr);

              if (data.token) {
                // Streaming token
                fullContent += data.token;
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantMessageId
                      ? { ...m, content: fullContent, isStreaming: true }
                      : m
                  )
                );
              } else if (data.status === "complete") {
                // Final metadata
                finalCitations = data.citations || [];
                finalConfidence = data.confidence_score;
                if (data.session_id) setSessionId(data.session_id);
              } else if (data.status === "refused") {
                // Refusal response
                fullContent = data.message || "I cannot find sufficient evidence in the provided documents.";
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantMessageId
                      ? { ...m, content: fullContent, isStreaming: false }
                      : m
                  )
                );
              } else if (data.error) {
                throw new Error(data.error);
              }
            } catch (parseError) {
              // Skip malformed SSE data
            }
          }
        }
      }

      // Finalize message
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMessageId
            ? {
                ...m,
                content: fullContent || "No response generated.",
                isStreaming: false,
                citations: finalCitations,
                confidence: finalConfidence,
              }
            : m
        )
      );
    } catch (err: any) {
      if (err.name === "AbortError") {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMessageId
              ? { ...m, content: "Request cancelled.", isStreaming: false }
              : m
          )
        );
      } else {
        const errorMessage = err.message || "An error occurred";
        setError(errorMessage);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMessageId
              ? {
                  ...m,
                  content: "",
                  isStreaming: false,
                  error: errorMessage,
                }
              : m
          )
        );
      }
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  }, [isLoading, sessionId]);

  const cancelStream = useCallback(() => {
    abortControllerRef.current?.abort();
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setSessionId(null);
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    sessionId,
    error,
    sendMessage,
    cancelStream,
    clearMessages,
  };
}
