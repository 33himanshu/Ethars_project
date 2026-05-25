"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import ChatInterface from "@/components/ChatInterface";
import DocumentUpload from "@/components/DocumentUpload";
import SearchHistory from "@/components/SearchHistory";
import { BookOpen, Upload, MessageSquare, Search } from "lucide-react";

type Tab = "chat" | "upload" | "history";

export default function HomePage() {
  const [activeTab, setActiveTab] = useState<Tab>("chat");

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: "chat", label: "Research Chat", icon: <MessageSquare size={16} /> },
    { id: "upload", label: "Upload Papers", icon: <Upload size={16} /> },
    { id: "history", label: "Search History", icon: <Search size={16} /> },
  ];

  return (
    <div className="flex flex-col h-screen bg-surface">
      {/* Header */}
      <header className="border-b border-surface-border bg-surface-card px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
              <BookOpen size={18} className="text-white" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-slate-100">
                RAG Research Assistant
              </h1>
              <p className="text-xs text-slate-400">
                AI-powered academic paper analysis
              </p>
            </div>
          </div>

          {/* Tab navigation */}
          <nav className="flex gap-1 bg-surface rounded-lg p-1" role="tablist">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                role="tab"
                aria-selected={activeTab === tab.id}
                aria-controls={`panel-${tab.id}`}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium
                  transition-all duration-200 focus:outline-none focus:ring-2
                  focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-surface
                  ${
                    activeTab === tab.id
                      ? "bg-primary-600 text-white shadow-sm"
                      : "text-slate-400 hover:text-slate-200 hover:bg-surface-card"
                  }
                `}
              >
                {tab.icon}
                <span className="hidden sm:inline">{tab.label}</span>
              </button>
            ))}
          </nav>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 overflow-hidden max-w-7xl mx-auto w-full">
        <AnimatePresence mode="wait">
          {activeTab === "chat" && (
            <motion.div
              key="chat"
              id="panel-chat"
              role="tabpanel"
              aria-labelledby="tab-chat"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2 }}
              className="h-full"
            >
              <ChatInterface />
            </motion.div>
          )}

          {activeTab === "upload" && (
            <motion.div
              key="upload"
              id="panel-upload"
              role="tabpanel"
              aria-labelledby="tab-upload"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2 }}
              className="h-full overflow-auto p-6"
            >
              <DocumentUpload />
            </motion.div>
          )}

          {activeTab === "history" && (
            <motion.div
              key="history"
              id="panel-history"
              role="tabpanel"
              aria-labelledby="tab-history"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2 }}
              className="h-full overflow-auto p-6"
            >
              <SearchHistory />
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}
