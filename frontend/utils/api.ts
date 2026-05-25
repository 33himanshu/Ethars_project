/**
 * API utility functions for the RAG Research Assistant frontend.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getAuthHeaders(): HeadersInit {
  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("access_token")
      : null;
  return {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function handleResponse(response: Response) {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: response.statusText }));
    throw new Error(error.detail || error.message || `HTTP ${response.status}`);
  }
  return response.json();
}

// ── Auth ──────────────────────────────────────────────────────────────────────

export async function login(email: string, password: string) {
  const response = await fetch(`${API_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await handleResponse(response);
  if (data.data?.access_token) {
    localStorage.setItem("access_token", data.data.access_token);
    localStorage.setItem("refresh_token", data.data.refresh_token);
  }
  return data;
}

export async function register(email: string, username: string, password: string) {
  const response = await fetch(`${API_URL}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, username, password }),
  });
  return handleResponse(response);
}

export function logout() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

// ── Documents ─────────────────────────────────────────────────────────────────

export async function uploadDocument(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_URL}/api/documents/upload`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: formData,
  });
  return handleResponse(response);
}

export async function listDocuments(page = 1, pageSize = 20) {
  const response = await fetch(
    `${API_URL}/api/documents?page=${page}&page_size=${pageSize}`,
    { headers: getAuthHeaders() }
  );
  return handleResponse(response);
}

export async function deleteDocument(documentId: string) {
  const response = await fetch(`${API_URL}/api/documents/${documentId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  return handleResponse(response);
}

// ── Search ────────────────────────────────────────────────────────────────────

export async function semanticSearch(
  query: string,
  topK = 5,
  year?: number,
  author?: string
) {
  const params = new URLSearchParams({ q: query, top_k: String(topK) });
  if (year) params.append("year", String(year));
  if (author) params.append("author", author);

  const response = await fetch(`${API_URL}/api/search?${params}`, {
    headers: getAuthHeaders(),
  });
  return handleResponse(response);
}

export async function getCitation(chunkId: string) {
  const response = await fetch(`${API_URL}/api/citations/${chunkId}`, {
    headers: getAuthHeaders(),
  });
  return handleResponse(response);
}

// ── Chat history ──────────────────────────────────────────────────────────────

export async function getChatHistory(sessionId: string) {
  const response = await fetch(`${API_URL}/api/chat/history/${sessionId}`, {
    headers: getAuthHeaders(),
  });
  return handleResponse(response);
}

export async function clearChatHistory(sessionId: string) {
  const response = await fetch(`${API_URL}/api/chat/history/${sessionId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  return handleResponse(response);
}
