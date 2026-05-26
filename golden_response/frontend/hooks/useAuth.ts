"use client";

import { useState, useEffect, useCallback } from "react";
import { login, register, logout } from "@/utils/api";

interface AuthUser {
  email: string;
  username: string;
  role: "researcher" | "admin";
}

export function useAuth() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check for existing token on mount
  useEffect(() => {
    const token =
      typeof window !== "undefined"
        ? localStorage.getItem("access_token")
        : null;
    if (token) {
      // Decode JWT payload (no verification — just for display)
      try {
        const payload = JSON.parse(atob(token.split(".")[1]));
        if (payload.exp * 1000 > Date.now()) {
          setUser({
            email: payload.email || "",
            username: payload.username || "",
            role: payload.role || "researcher",
          });
        } else {
          // Token expired
          logout();
        }
      } catch {
        logout();
      }
    }
  }, []);

  const signIn = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await login(email, password);
      // Decode user info from token
      const token = data.data.access_token;
      const payload = JSON.parse(atob(token.split(".")[1]));
      setUser({
        email,
        username: payload.username || email.split("@")[0],
        role: payload.role || "researcher",
      });
      return true;
    } catch (err: any) {
      setError(err.message || "Login failed");
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const signUp = useCallback(
    async (email: string, username: string, password: string) => {
      setIsLoading(true);
      setError(null);
      try {
        await register(email, username, password);
        // Auto-login after registration
        return await signIn(email, password);
      } catch (err: any) {
        setError(err.message || "Registration failed");
        return false;
      } finally {
        setIsLoading(false);
      }
    },
    [signIn]
  );

  const signOut = useCallback(() => {
    logout();
    setUser(null);
  }, []);

  const isAuthenticated = user !== null;

  return {
    user,
    isAuthenticated,
    isLoading,
    error,
    signIn,
    signUp,
    signOut,
  };
}
