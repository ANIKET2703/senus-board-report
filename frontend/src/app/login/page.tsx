"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { login } from "@/lib/api";
import { TrendingUp } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("ceo@senus.com");
  const [password, setPassword] = useState("senus2030");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true); setError(null);
    try {
      await login(email, password);
      router.push("/dashboard");
    } catch {
      setError("Invalid email or password");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--accent)]">
            <TrendingUp className="h-6 w-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight">Senus PLC Board Report</h1>
          <p className="subtle mt-2">AI-native performance reporting for Management, the Board, Investors and Credit Providers</p>
        </div>
        <form onSubmit={submit} className="panel space-y-4 p-6">
          <div>
            <label className="subtle mb-1 block">Email</label>
            <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required
              className="w-full rounded-lg border border-[var(--border)] bg-[var(--panel-2)] px-3 py-2 outline-none focus:border-[var(--accent)]" />
          </div>
          <div>
            <label className="subtle mb-1 block">Password</label>
            <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" required
              className="w-full rounded-lg border border-[var(--border)] bg-[var(--panel-2)] px-3 py-2 outline-none focus:border-[var(--accent)]" />
          </div>
          {error && <p className="text-sm text-[var(--neg)]">{error}</p>}
          <button disabled={loading}
            className="w-full rounded-lg bg-[var(--accent)] py-2.5 font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-50">
            {loading ? "Signing in…" : "Sign in"}
          </button>
          <p className="subtle text-center text-xs">Demo access: ceo@senus.com / senus2030</p>
        </form>
      </div>
    </main>
  );
}
