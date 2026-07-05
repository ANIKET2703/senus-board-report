"use client";
import { FileSearch } from "lucide-react";
import { eur } from "@/lib/format";
import type { FactRow } from "@/lib/api";

/** Statement table where every value shows its extraction provenance on hover. */
export default function ProvenanceTable({ rows, periods }: { rows: FactRow[]; periods: string[] }) {
  const lines = Array.from(new Map(rows.map((r) => [r.line_code, r.label])).entries());
  const byKey = new Map(rows.map((r) => [`${r.line_code}|${r.period}`, r]));
  return (
    <div className="panel overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-[var(--border)] text-left">
            <th className="p-3 font-medium text-[var(--muted)]">Line item</th>
            {periods.map((p) => <th key={p} className="p-3 text-right font-medium text-[var(--muted)]">{p}</th>)}
          </tr>
        </thead>
        <tbody>
          {lines.map(([code, label]) => (
            <tr key={code} className="border-b border-[var(--border)] last:border-0 hover:bg-[var(--panel-2)]">
              <td className="p-3">{label}</td>
              {periods.map((p) => {
                const fact = byKey.get(`${code}|${p}`);
                return (
                  <td key={p} className="group relative p-3 text-right tabular-nums">
                    {fact ? (
                      <>
                        <span className={fact.value < 0 ? "text-[var(--neg)]" : ""}>{
                          fact.unit === "EUR" ? eur(fact.value, false) : fact.value.toLocaleString()}</span>
                        <span className="pointer-events-none absolute right-0 top-full z-10 hidden w-72 rounded-lg border border-[var(--border)] bg-[var(--panel-2)] p-3 text-left text-xs shadow-xl group-hover:block">
                          <span className="mb-1 flex items-center gap-1 font-medium text-[var(--accent)]">
                            <FileSearch className="h-3 w-3" /> Source provenance
                          </span>
                          {fact.source.document}<br />
                          Page {fact.source.page} · extracted via {fact.source.method === "vision" ? "Claude vision (scanned page)" : "text layer"} · confidence {(fact.source.confidence * 100).toFixed(0)}%
                        </span>
                      </>
                    ) : "-"}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
