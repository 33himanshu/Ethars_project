"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Loader2, Eye, EyeOff, BookOpen } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface AuthModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

type Mode = "login" | "register";

export default function AuthModal({ onClose, onSuccess }: AuthModalProps) {
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const { signIn, signUp, isLoading, error } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    let success = false;
    if (mode === "login") {
      success = await signIn(email, password);
    } else {
      success = await signUp(email, username, password);
    }
    if (success) onSuccess();
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="auth-modal-title"
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        transition={{ duration: 0.2 }}
        className="bg-surface-card border border-surface-border rounded-2xl p-8 w-full max-w-md mx-4 shadow-2xl"
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-primary-600 rounded-xl flex items-center justify-center">
              <BookOpen size={18} className="text-white" />
            </div>
            <div>
              <h2
                id="auth-modal-title"
                className="text-lg font-semibold text-slate-100"
              >
                {mode === "login" ? "Sign In" : "Create Account"}
              </h2>
              <p className="text-xs text-slate-400">RAG Research Assistant</p>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close"
            className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-400
                       hover:text-slate-200 hover:bg-surface transition-colors
                       focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <X size={16} />
          </button>
        </div>

        {/* Tab switcher */}
        <div className="flex bg-surface rounded-lg p-1 mb-6">
          {(["login", "register"] as Mode[]).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`flex-1 py-2 rounded-md text-sm font-medium transition-all duration-200
                          focus:outline-none focus:ring-2 focus:ring-primary-500
                          ${
                            mode === m
                              ? "bg-primary-600 text-white"
                              : "text-slate-400 hover:text-slate-200"
                          }`}
            >
              {m === "login" ? "Sign In" : "Register"}
            </button>
          ))}
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-slate-300 mb-1.5"
            >
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              placeholder="researcher@university.edu"
              className="w-full bg-surface border border-surface-border rounded-lg px-4 py-2.5
                         text-sm text-slate-100 placeholder-slate-500
                         focus:outline-none focus:ring-2 focus:ring-primary-500
                         focus:border-transparent transition-colors"
            />
          </div>

          <AnimatePresence>
            {mode === "register" && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.2 }}
              >
                <label
                  htmlFor="username"
                  className="block text-sm font-medium text-slate-300 mb-1.5"
                >
                  Username
                </label>
                <input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required={mode === "register"}
                  autoComplete="username"
                  placeholder="researcher_name"
                  className="w-full bg-surface border border-surface-border rounded-lg px-4 py-2.5
                             text-sm text-slate-100 placeholder-slate-500
                             focus:outline-none focus:ring-2 focus:ring-primary-500
                             focus:border-transparent transition-colors"
                />
              </motion.div>
            )}
          </AnimatePresence>

          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-slate-300 mb-1.5"
            >
              Password
            </label>
            <div className="relative">
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete={mode === "login" ? "current-password" : "new-password"}
                placeholder="••••••••"
                className="w-full bg-surface border border-surface-border rounded-lg px-4 py-2.5
                           pr-11 text-sm text-slate-100 placeholder-slate-500
                           focus:outline-none focus:ring-2 focus:ring-primary-500
                           focus:border-transparent transition-colors"
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? "Hide password" : "Show password"}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400
                           hover:text-slate-200 transition-colors focus:outline-none"
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {/* Error message */}
          <AnimatePresence>
            {error && (
              <motion.p
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="text-sm text-red-400 bg-red-900/20 border border-red-800
                           rounded-lg px-3 py-2"
                role="alert"
              >
                {error}
              </motion.p>
            )}
          </AnimatePresence>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-primary-600 hover:bg-primary-700 disabled:opacity-50
                       disabled:cursor-not-allowed text-white font-medium py-2.5 rounded-lg
                       transition-colors duration-200 flex items-center justify-center gap-2
                       focus:outline-none focus:ring-2 focus:ring-primary-500
                       focus:ring-offset-2 focus:ring-offset-surface-card"
          >
            {isLoading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                {mode === "login" ? "Signing in..." : "Creating account..."}
              </>
            ) : mode === "login" ? (
              "Sign In"
            ) : (
              "Create Account"
            )}
          </button>
        </form>

        <p className="text-xs text-slate-500 text-center mt-4">
          {mode === "login" ? (
            <>
              Don't have an account?{" "}
              <button
                onClick={() => setMode("register")}
                className="text-primary-400 hover:text-primary-300 underline"
              >
                Register
              </button>
            </>
          ) : (
            <>
              Already have an account?{" "}
              <button
                onClick={() => setMode("login")}
                className="text-primary-400 hover:text-primary-300 underline"
              >
                Sign in
              </button>
            </>
          )}
        </p>
      </motion.div>
    </div>
  );
}
