"use client";
import { useRef, useState } from "react";
import { api } from "@/lib/api";
import { Send, BookOpenCheck } from "lucide-react";

interface Citation { content: string; document: string; page: number | null; score: number }
interface Msg { role: "user" | "assistant"; text: string; citations?: Citation[] }

const SUGGESTIONS = [
  "What was FY25 revenue and how fast is it growing?",
  "How long is the cash runway?",
  "What did Senus pay for Loamin?",
  "Is the company on track for its Senus 2030 targets?",
  "What are the biggest risks for a credit provider?",
];

export default function Chat() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const bottom = useRef<HTMLDivElement>(null);

  async function ask(q: string) {
    if (!q.trim() || busy) return;
    setMessages((m) => [...m, { role: "user", text: q }]);
    setInput(""); setBusy(true);
    try {
      const res = await api<{ answer: string; citations: Citation[] }>("/api/chat", {
        method: "POST", body: JSON.stringify({ question: q }),
      });
      setMessages((m) => [...m, { role: "assistant", text: res.answer, citations: res.citations }]);
    } catch {
      setMessages((m) => [...m, { role: "assistant", text: "Something went wrong - please retry." }]);
    } finally {
      setBusy(false);
      setTimeout(() => bottom.current?.scrollIntoView({ behavior: "smooth" }), 50);
    }
  }

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col space-y-4">
      <header>
        <h1 className="text-2xl font-bold tracking-tight">Ask the Board Pack</h1>
        <p className="subtle mt-1">
          Retrieval-augmented Q&A over the source filings. Answers are grounded in retrieved passages
          and validated metrics, with page-level citations.
        </p>
      </header>

      <div className="panel flex-1 space-y-4 overflow-y-auto p-5">
        {messages.length === 0 && (
          <div className="space-y-2">
            <p className="subtle text-sm">Suggested questions</p>
            {SUGGESTIONS.map((s) => (
              <button key={s} onClick={() => ask(s)}
                className="block rounded-lg border border-[var(--border)] px-3 py-2 text-left text-sm text-[var(--muted)] hover:border-[var(--accent)] hover:text-[var(--text)]">
                {s}
              </button>
            ))}
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "flex justify-end" : ""}>
            <div className={`max-w-2xl rounded-xl p-4 text-sm leading-relaxed ${
              m.role === "user" ? "bg-[var(--accent)] text-white" : "bg-[var(--panel-2)]"}`}>
              <p className="whitespace-pre-wrap">{m.text}</p>
              {m.citations && m.citations.length > 0 && (
                <details className="mt-3 border-t border-[var(--border)] pt-2">
                  <summary className="flex cursor-pointer items-center gap-1 text-xs text-[var(--muted)]">
                    <BookOpenCheck className="h-3 w-3" /> {m.citations.length} source passages retrieved
                  </summary>
                  <ul className="mt-2 space-y-2">
                    {m.citations.map((c, j) => (
                      <li key={j} className="rounded bg-black/20 p-2 text-xs text-[var(--muted)]">
                        <span className="font-medium text-[var(--text)]">{c.document}, p.{c.page}</span>
                        <p className="mt-1 line-clamp-3">{c.content}</p>
                      </li>
                    ))}
                  </ul>
                </details>
              )}
            </div>
          </div>
        ))}
        {busy && <p className="subtle animate-pulse text-sm">Retrieving sources and drafting answer…</p>}
        <div ref={bottom} />
      </div>

      <form onSubmit={(e) => { e.preventDefault(); ask(input); }} className="flex gap-2">
        <input value={input} onChange={(e) => setInput(e.target.value)}
          placeholder="Ask anything about Senus PLC's performance…"
          className="flex-1 rounded-xl border border-[var(--border)] bg-[var(--panel)] px-4 py-3 text-sm outline-none focus:border-[var(--accent)]" />
        <button disabled={busy || !input.trim()}
          className="rounded-xl bg-[var(--accent)] px-4 text-white transition-opacity hover:opacity-90 disabled:opacity-40">
          <Send className="h-4 w-4" />
        </button>
      </form>
    </div>
  );
}
