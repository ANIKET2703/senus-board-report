/** Typed API client. JWT kept in localStorage (demo-grade by design). */
export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {}),
      ...init?.headers,
    },
  });
  if (res.status === 401 && typeof window !== "undefined") {
    localStorage.removeItem("token");
    window.location.href = "/login";
  }
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
  return res.json();
}

export async function login(email: string, password: string) {
  const body = new URLSearchParams({ username: email, password });
  const res = await fetch(`${API_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!res.ok) throw new Error("Invalid credentials");
  const data = await res.json();
  localStorage.setItem("token", data.access_token);
  localStorage.setItem("user", JSON.stringify(data.user));
  return data;
}

export interface Metric {
  key: string; label: string; value: number | null; unit: string;
  period: string; caveat: string | null; inputs: Record<string, number>;
}
export type MetricCategories = Record<"growth" | "profitability" | "cash" | "solvency" | "returns", Metric[]>;

export interface FactRow {
  id: number; period: string; line_code: string; label: string; value: number; unit: string;
  source: { document: string; filename: string; page: number | null; method: string; confidence: number };
}
