"use client";

import { useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { motion } from "framer-motion";

interface StreamingMessageProps {
  content: string;
  isStreaming?: boolean;
  onCitationClick?: () => void;
}

export default function StreamingMessage({
  content,
  isStreaming = false,
  onCitationClick,
}: StreamingMessageProps) {
  const cursorRef = useRef<HTMLSpanElement>(null);

  // Process citation references in text: [Author, Year, chunk_id]
  // (used for future inline citation highlighting)
  const _processedContent = content.replace(
    /\[([^\]]+?,\s*\d{4},\s*[^\]]+?)\]/g,
    (match) => {
      return `<span class="citation-ref" role="button" tabindex="0" aria-label="View citation">${match}</span>`;
    }
  );

  return (
    <div className="relative">
      <div
        className="prose-dark text-sm leading-relaxed max-w-none"
        onClick={onCitationClick}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            onCitationClick?.();
          }
        }}
      >
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            // Custom paragraph to handle citation spans
            p: ({ children }) => (
              <p className="mb-3 last:mb-0 text-slate-200">{children}</p>
            ),
            // Code blocks
            code: ({ className, children, ...props }) => {
              const isInline = !className;
              return isInline ? (
                <code
                  className="bg-surface px-1.5 py-0.5 rounded text-primary-300 text-xs font-mono"
                  {...props}
                >
                  {children}
                </code>
              ) : (
                <code
                  className="block bg-surface p-4 rounded-lg text-xs font-mono text-slate-300 overflow-x-auto"
                  {...props}
                >
                  {children}
                </code>
              );
            },
            // Headings
            h1: ({ children }) => (
              <h1 className="text-lg font-bold text-slate-100 mb-3">{children}</h1>
            ),
            h2: ({ children }) => (
              <h2 className="text-base font-semibold text-slate-100 mb-2">{children}</h2>
            ),
            h3: ({ children }) => (
              <h3 className="text-sm font-semibold text-slate-200 mb-2">{children}</h3>
            ),
            // Lists
            ul: ({ children }) => (
              <ul className="list-disc list-inside space-y-1 mb-3 text-slate-200">{children}</ul>
            ),
            ol: ({ children }) => (
              <ol className="list-decimal list-inside space-y-1 mb-3 text-slate-200">{children}</ol>
            ),
            li: ({ children }) => (
              <li className="text-sm">{children}</li>
            ),
            // Blockquote
            blockquote: ({ children }) => (
              <blockquote className="border-l-2 border-primary-500 pl-4 italic text-slate-400 my-3">
                {children}
              </blockquote>
            ),
            // Strong
            strong: ({ children }) => (
              <strong className="font-semibold text-slate-100">{children}</strong>
            ),
          }}
        >
          {content}
        </ReactMarkdown>
      </div>

      {/* Streaming cursor */}
      {isStreaming && (
        <motion.span
          ref={cursorRef}
          className="inline-block w-0.5 h-4 bg-primary-400 ml-0.5 align-middle"
          animate={{ opacity: [1, 0, 1] }}
          transition={{ duration: 0.8, repeat: Infinity }}
          aria-hidden="true"
        />
      )}
    </div>
  );
}
