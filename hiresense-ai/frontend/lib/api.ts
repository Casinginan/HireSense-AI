const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export class ApiError extends Error {
  status: number;
  details: unknown;
  constructor(message: string, status: number, details?: unknown) {
    super(message);
    this.status = status;
    this.details = details;
  }
}

function getStoredToken(key: "access_token" | "refresh_token"): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(key);
}

function storeTokens(access: string, refresh?: string) {
  window.localStorage.setItem("access_token", access);
  if (refresh) window.localStorage.setItem("refresh_token", refresh);
}

export function clearSession() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem("access_token");
  window.localStorage.removeItem("refresh_token");
  window.localStorage.removeItem("user");
}

async function tryRefresh(): Promise<string | null> {
  const refreshToken = getStoredToken("refresh_token");
  if (!refreshToken) return null;
  const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!res.ok) return null;
  const data = await res.json();
  storeTokens(data.access_token);
  return data.access_token as string;
}

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  isForm?: boolean;
  skipAuth?: boolean;
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, isForm = false, skipAuth = false } = options;

  const doFetch = async (token: string | null): Promise<Response> => {
    const headers: Record<string, string> = {};
    if (!isForm) headers["Content-Type"] = "application/json";
    if (token && !skipAuth) headers["Authorization"] = `Bearer ${token}`;

    return fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: body ? (isForm ? (body as FormData) : JSON.stringify(body)) : undefined,
    });
  };

  let token = skipAuth ? null : getStoredToken("access_token");
  let res = await doFetch(token);

  if (res.status === 401 && !skipAuth) {
    const newToken = await tryRefresh();
    if (newToken) {
      res = await doFetch(newToken);
    }
  }

  if (!res.ok) {
    let detail: unknown = res.statusText;
    try {
      const errBody = await res.json();
      detail = errBody.detail ?? errBody;
    } catch {
      /* response had no JSON body */
    }
    const message = typeof detail === "string" ? detail : JSON.stringify(detail);
    throw new ApiError(message, res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export async function login(email: string, password: string) {
  const data = await apiRequest<{ access_token: string; refresh_token: string }>("/auth/login", {
    method: "POST",
    body: { email, password },
    skipAuth: true,
  });
  storeTokens(data.access_token, data.refresh_token);
  const me = await apiRequest<{ id: string; full_name: string; email: string; role: string }>("/auth/me");
  window.localStorage.setItem("user", JSON.stringify(me));
  return me;
}

export function getCurrentUser(): { id: string; full_name: string; email: string; role: string } | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem("user");
  return raw ? JSON.parse(raw) : null;
}

export function isAuthenticated(): boolean {
  return !!getStoredToken("access_token");
}
