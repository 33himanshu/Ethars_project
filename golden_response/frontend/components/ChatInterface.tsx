"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Loader2, AlertCircle } from "lucide-react";
import StreamingMessage from "./StreamingMessage";
import CitationPanel from "./CitationPanel";
import TypingIndicator from "./TypingIndicator";
import { useChat } from "@/hooks/useChat";

interface Citation {
  chunk_id: string;
  title: string;
  authors: string[];
  year?: number;
  page_number?: number;
  snippet: string;
  is_verified: boolean;
}

export default function ChatInterface() {
  const [input, setInput] = useState("");
  const [selectedCitations, setSelectedCitations] = useState<Citation[]>([]);
  const [showCitationPanel, setShowCitationPanel] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const { messages, isLoading, sessionId, sendMessage, error } = useChat();

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      const query = input.trim();
      if (!query || isLoading) return;
      setInput("");
      await sendMessage(query);
    },
    [input, isLoading, sendMessage]
  );

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as unknown as React.FormEvent);
    }
  };

  const handleCitationClick = (citations: Citation[]) => {
    setSelectedCitations(citations);
    setShowCitationPanel(true);
  };

  return (
    <div className="flex h-full">
      {/* Chat area */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Messages */}
        <div
          className="flex-1 overflow-y-auto px-4 py-6 space-y-6"
          role="log"
          aria-label="Conversation history"
          aria-live="polite"
        >
          {messages.length === 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex flex-col items-center justify-center h-full text-center"
            >
              <div className="w-16 h-16 bg-primary-600/20 rounded-2xl flex items-center justify-center mb-4">
                <span className="text-3xl">🔬</span>
              </div>
              <h2 className="text-xl font-semibold text-slate-200 mb-2">
                Ask about your research papers
              </h2>
              <p className="text-slate-400 max-w-md text-sm">
                Upload academic papers and ask questions. The assistant will
                retrieve relevant passages and provide citation-aware answers.
              </p>
              <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg w-full">
                {[
                  "What attention mechanism is proposed in this paper?",
                  "How does the Transformer differ from RNNs?",
                  "What BLEU score was achieved on English-German translation?",
                  "Explain the multi-head attention mechanism",
                ].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => setInput(suggestion)}
                    className="text-left px-4 py-3 bg-surface-card border border-surface-border
                               rounded-lg text-sm text-slate-300 hover:border-primary-500
                               hover:text-slate-100 transition-all duration-200"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </motion.div>
          )}

          <AnimatePresence initial={false}>
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                className={`flex gap-3 ${
                  message.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                {message.role === "assistant" && (
                  <div
                    className="w-8 h-8 bg-primary-600 rounded-full flex items-center
                                justify-center flex-shrink-0 mt-1"
                    aria-hidden="true"
                  >
                    <span className="text-xs font-bold text-white">AI</span>
                  </div>
                )}

                <div
                  className={`max-w-[80%] ${
                    message.role === "user" ? "items-end" : "items-start"
                  } flex flex-col gap-2`}
                >
                  <div
                    className={`rounded-2xl px-4 py-3 ${
                      message.role === "user"
                        ? "bg-primary-600 text-white rounded-tr-sm"
                        : "bg-surface-card border border-surface-border rounded-tl-sm"
                    }`}
                  >
                    {message.role === "assistant" ? (
                      <StreamingMessage
                        content={message.content}
                        isStreaming={message.isStreaming}
                        onCitationClick={() =>
                          message.citations &&
                          handleCitationClick(message.citations)
                        }
                      />
                    ) : (
                      <p className="text-sm leading-relaxed">{message.content}</p>
                    )}
                  </div>

                  {/* Confidence + citation count */}
                  {message.role === "assistant" &&
                    !message.isStreaming &&
                    message.citations &&
                    message.citations.length > 0 && (
                      <div className="flex items-center gap-3">
                        <button
                          onClick={() =>
                            handleCitationClick(message.citations!)
                          }
                          className="text-xs text-primary-400 hover:text-primary-300
                                     underline underline-offset-2 transition-colors"
                          aria-label={`View ${message.citations.length} citations`}
                        >
                          {message.citations.length} source
                          {message.citations.length !== 1 ? "s" : ""}
                        </button>
                        {message.confidence !== undefined && (
                          <span className="text-xs text-slate-500">
                            Confidence:{" "}
                            {(message.confidence * 100).toFixed(0)}%
                          </span>
                        )}
                      </div>
                    )}

                  {message.error && (
                    <div className="flex items-center gap-2 text-red-400 text-xs">
                      <AlertCircle size={12} />
                      <span>{message.error}</span>
                    </div>
                  )}
                </div>

                {message.role === "user" && (
                  <div
                    className="w-8 h-8 bg-slate-600 rounded-full flex items-center
                                justify-center flex-shrink-0 mt-1"
                    aria-hidden="true"
                  >
                    <span className="text-xs font-bold text-white">U</span>
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Typing indicator */}
          {isLoading && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex gap-3 justify-start"
            >
              <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center flex-shrink-0">
                <span className="text-xs font-bold text-white">AI</span>
              </div>
              <div className="bg-surface-card border border-surface-border rounded-2xl rounded-tl-sm px-4 py-3">
                <TypingIndicator />
              </div>
            </motion.div>
          )}

          {error && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-center gap-2 text-red-400 text-sm bg-red-900/20
                         border border-red-800 rounded-lg px-4 py-3"
              role="alert"
            >
              <AlertCircle size={16} />
              <span>{error}</span>
            </motion.div>
          )}

          <div ref={messagesEndRef} aria-hidden="true" />
        </div>

        {/* Input area */}
        <div className="border-t border-surface-border bg-surface-card px-4 py-4">
          {sessionId && (
            <p className="text-xs text-slate-500 mb-2">
              Session: {sessionId.slice(0, 8)}...
            </p>
          )}
          <form onSubmit={handleSubmit} className="flex gap-3 items-end">
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about your research papers... (Enter to send, Shift+Enter for new line)"
                rows={1}
                disabled={isLoading}
                aria-label="Chat input"
                className="w-full bg-surface border border-surface-border rounded-xl px-4 py-3
                           text-sm text-slate-100 placeholder-slate-500 resize-none
                           focus:outline-none focus:ring-2 focus:ring-primary-500
                           focus:border-transparent disabled:opacity-50
                           min-h-[48px] max-h-[200px] overflow-y-auto"
                style={{
                  height: "auto",
                  minHeight: "48px",
                }}
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement;
                  target.style.height = "auto";
                  target.style.height = `${Math.min(target.scrollHeight, 200)}px`;
                }}
              />
            </div>
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              aria-label="Send message"
              className="w-12 h-12 bg-primary-600 hover:bg-primary-700 disabled:opacity-50
                         disabled:cursor-not-allowed rounded-xl flex items-center justify-center
                         transition-colors duration-200 focus:outline-none focus:ring-2
                         focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-surface-card
                         flex-shrink-0"
            >
              {isLoading ? (
                <Loader2 size={18} className="text-white animate-spin" />
              ) : (
                <Send size={18} className="text-white" />
              )}
            </button>
          </form>
        </div>
      </div>

      {/* Citation panel */}
      <AnimatePresence>
        {showCitationPanel && (
          <CitationPanel
            citations={selectedCitations}
            onClose={() => setShowCitationPanel(false)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
