"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Clock, Trash2, MessageSquare, ChevronDown, ChevronUp } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

interface HistoryTurn {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  citations?: any[];
  confidence_score?: number;
}

interface SessionHistory {
  session_id: string;
  history: HistoryTurn[];
  turn_count: number;
}

export default function SearchHistory() {
  const [sessions, setSessions] = useState<SessionHistory[]>([]);
  const [expandedSession, setExpandedSession] = useState<string | null>(null);

  // In a real app, you'd fetch sessions from the API
  // For demo, we show a placeholder
  const demoSessions: SessionHistory[] = [
    {
      session_id: "demo-session-1",
      turn_count: 3,
      history: [
        {
          role: "user",
          content: "What attention mechanism is proposed in this paper?",
          timestamp: new Date(Date.now() - 3600000).toISOString(),
        },
        {
          role: "assistant",
          content: "The paper proposes the **Transformer** architecture based entirely on self-attention mechanisms...",
          timestamp: new Date(Date.now() - 3590000).toISOString(),
          confidence_score: 0.87,
          citations: [{ chunk_id: "doc1_chunk_3", title: "Attention Is All You Need" }],
        },
        {
          role: "user",
          content: "How does it differ from RNNs?",
          timestamp: new Date(Date.now() - 3500000).toISOString(),
        },
      ],
    },
  ];

  useEffect(() => {
    setSessions(demoSessions);
  }, []);

  const clearSession = (sessionId: string) => {
    setSessions((prev) => prev.filter((s) => s.session_id !== sessionId));
  };

  const toggleExpand = (sessionId: string) => {
    setExpandedSession((prev) => (prev === sessionId ? null : sessionId));
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-100 mb-1">
          Search History
        </h2>
        <p className="text-sm text-slate-400">
          Your recent research conversations. Sessions expire after 24 hours.
        </p>
      </div>

      {sessions.length === 0 ? (
        <div className="text-center py-16">
          <Clock size={40} className="text-slate-600 mx-auto mb-4" />
          <p className="text-slate-400">No search history yet</p>
          <p className="text-slate-500 text-sm mt-1">
            Start a conversation in the Research Chat tab
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {sessions.map((session) => (
            <motion.div
              key={session.session_id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-surface-card border border-surface-border rounded-xl overflow-hidden"
            >
              {/* Session header */}
              <div className="flex items-center justify-between px-4 py-3">
                <button
                  onClick={() => toggleExpand(session.session_id)}
                  className="flex items-center gap-3 flex-1 text-left focus:outline-none
                             focus:ring-2 focus:ring-primary-500 rounded-md"
                  aria-expanded={expandedSession === session.session_id}
                  aria-controls={`session-${session.session_id}`}
                >
                  <div className="w-8 h-8 bg-primary-900/50 rounded-lg flex items-center justify-center">
                    <MessageSquare size={14} className="text-primary-400" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-200">
                      Session {session.session_id.slice(0, 8)}...
                    </p>
                    <p className="text-xs text-slate-500">
                      {session.turn_count} turns •{" "}
                      {session.history[0]?.timestamp
                        ? formatDistanceToNow(new Date(session.history[0].timestamp), {
                            addSuffix: true,
                          })
                        : "Unknown time"}
                    </p>
                  </div>
                  <div className="ml-auto mr-2 text-slate-500">
                    {expandedSession === session.session_id ? (
                      <ChevronUp size={16} />
                    ) : (
                      <ChevronDown size={16} />
                    )}
                  </div>
                </button>
                <button
                  onClick={() => clearSession(session.session_id)}
                  aria-label={`Delete session ${session.session_id.slice(0, 8)}`}
                  className="w-7 h-7 rounded-md flex items-center justify-center
                             text-slate-500 hover:text-red-400 hover:bg-red-900/20
                             transition-colors focus:outline-none focus:ring-2
                             focus:ring-red-500"
                >
                  <Trash2 size={14} />
                </button>
              </div>

              {/* Session turns */}
              <AnimatePresence>
                {expandedSession === session.session_id && (
                  <motion.div
                    id={`session-${session.session_id}`}
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="border-t border-surface-border overflow-hidden"
                  >
                    <div className="p-4 space-y-3 max-h-80 overflow-y-auto">
                      {session.history.map((turn, i) => (
                        <div
                          key={i}
                          className={`flex gap-2 ${
                            turn.role === "user" ? "justify-end" : "justify-start"
                          }`}
                        >
                          <div
                            className={`max-w-[85%] rounded-xl px-3 py-2 text-xs ${
                              turn.role === "user"
                                ? "bg-primary-600/30 text-slate-200"
                                : "bg-surface text-slate-300"
                            }`}
                          >
                            <p className="leading-relaxed line-clamp-3">
                              {turn.content}
                            </p>
                            {turn.confidence_score && (
                              <p className="text-slate-500 mt-1">
                                Confidence: {(turn.confidence_score * 100).toFixed(0)}%
                              </p>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
