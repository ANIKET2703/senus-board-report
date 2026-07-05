"use client";
import { useEffect, useState } from "react";
import { api, API_URL } from "@/lib/api";
import { FileText, ScanEye, FileType2, UserCheck, AlertTriangle } from "lucide-react";

interface Doc {
  id: number; filename: string; title: string; doc_type: string;
  published_date: string; pages: number; has_text_layer: boolean; facts_extracted: number;
}
interface DocFact {
  id: number; period: string; statement: string; label: string;
  value: number; page: number | null; method: string; confidence: number;
}
interface ReviewQueue {
  threshold: number;
  items: { id: number; period: string; line_code: string; label: string; value: number;
           page: number | null; document: string; method: string; confidence: number }[];
}

export default function Documents() {
  const [docs, setDocs] = useState<Doc[]>([]);
  const [selected, setSelected] = useState<Doc | null>(null);
  const [facts, setFacts] = useState<DocFact[]>([]);
  const [queue, setQueue] = useState<ReviewQueue | null>(null);

  useEffect(() => {
    api<Doc[]>("/api/documents").then(setDocs);
    api<ReviewQueue>("/api/validation/review-queue").then(setQueue).catch(() => {});
  }, []);
  useEffect(() => {
    if (selected) api<DocFact[]>(`/api/documents/${selected.id}/facts`).then(setFacts);
  }, [selected]);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold tracking-tight">Documents & Audit Trail</h1>
        <p className="subtle mt-1">
          Every figure in this report traces to a published source document. Scanned documents
          (no text layer) were extracted with Claude vision; text documents via the PDF text layer.
        </p>
      </header>

      {queue && (
        <div className="panel p-5">
          <h2 className="h-title mb-2 flex items-center gap-2">
            <UserCheck className="h-4 w-4 text-[var(--accent)]" /> Human review queue
          </h2>
          {queue.items.length ? (
            <>
              <p className="subtle mb-3 text-xs">
                Facts below {(queue.threshold * 100).toFixed(0)}% extraction confidence after
                two-pass verification. These are excluded from commentary until signed off.
              </p>
              <ul className="space-y-2">
                {queue.items.map((f) => (
                  <li key={f.id} className="flex flex-wrap items-center gap-2 rounded-lg border border-amber-500/30 bg-amber-500/5 p-3 text-sm">
                    <AlertTriangle className="h-4 w-4 shrink-0 text-[var(--warn)]" />
                    <span className="font-medium">{f.period} · {f.label}</span>
                    <span className="tabular-nums">{f.value.toLocaleString()}</span>
                    <span className="subtle text-xs">{f.document} p.{f.page} · {f.method} · {(f.confidence * 100).toFixed(0)}%</span>
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <p className="subtle text-sm">
              Queue is empty: every fact in the store is at ≥ {(queue.threshold * 100).toFixed(0)}%
              confidence. Values extracted below the threshold are independently re-read from their
              source page (two-pass verification); anything still uncertain lands here for human
              sign-off before it can reach commentary. All committed facts were additionally
              human-verified against the filings.
            </p>
          )}
        </div>
      )}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {docs.map((d) => (
          <button key={d.id} onClick={() => setSelected(d)}
            className={`panel panel-hover p-4 text-left ${selected?.id === d.id ? "border-[var(--accent)]" : ""}`}>
            <div className="mb-2 flex items-center gap-2">
              {d.has_text_layer
                ? <FileType2 className="h-4 w-4 text-[var(--pos)]" />
                : <ScanEye className="h-4 w-4 text-[var(--warn)]" />}
              <span className="text-xs uppercase tracking-wide text-[var(--muted)]">{d.doc_type.replace("_", " ")}</span>
            </div>
            <p className="text-sm font-medium leading-snug">{d.title}</p>
            <p className="subtle mt-2 text-xs">
              {d.published_date} · {d.pages} pages · {d.has_text_layer ? "text layer" : "scanned - vision extraction"}
            </p>
            <p className="mt-1 text-xs text-[var(--accent)]">{d.facts_extracted} facts extracted</p>
          </button>
        ))}
      </div>
      {selected && (
        <div className="panel p-5">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="h-title flex items-center gap-2"><FileText className="h-4 w-4" /> {selected.title}</h2>
            <a className="rounded-lg border border-[var(--border)] px-3 py-1.5 text-sm hover:border-[var(--accent)]"
              href={`${API_URL}/api/documents/${selected.id}/pdf`} target="_blank" rel="noreferrer">
              Open source PDF
            </a>
          </div>
          {facts.length ? (
            <div className="max-h-96 overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-[var(--panel)]">
                  <tr className="border-b border-[var(--border)] text-left text-[var(--muted)]">
                    <th className="p-2">Period</th><th className="p-2">Statement</th><th className="p-2">Line</th>
                    <th className="p-2 text-right">Value</th><th className="p-2 text-right">Page</th><th className="p-2">Method</th>
                  </tr>
                </thead>
                <tbody>
                  {facts.map((f) => (
                    <tr key={f.id} className="border-b border-[var(--border)] last:border-0">
                      <td className="p-2">{f.period}</td>
                      <td className="p-2 uppercase">{f.statement}</td>
                      <td className="p-2">{f.label}</td>
                      <td className="p-2 text-right tabular-nums">{f.value.toLocaleString()}</td>
                      <td className="p-2 text-right">{f.page ?? "-"}</td>
                      <td className="p-2">{f.method}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : <p className="subtle text-sm">No structured facts extracted from this document (narrative/legal document).</p>}
        </div>
      )}
    </div>
  );
}
