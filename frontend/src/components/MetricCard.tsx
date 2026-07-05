"use client";
import { ArrowDownRight, ArrowUpRight, Info } from "lucide-react";
import { formatBy } from "@/lib/format";
import type { Metric } from "@/lib/api";

function computeDelta(metric: Metric, prior?: Metric | null): { text: string; up: boolean } | null {
  if (!prior || prior.value === null || metric.value === null) return null;
  if (metric.unit === "pct") {
    const pp = (metric.value - prior.value) * 100;
    return { text: `${pp >= 0 ? "+" : ""}${pp.toFixed(1)}pp vs ${prior.period}`, up: pp >= 0 };
  }
  if (metric.unit === "EUR" && prior.value !== 0) {
    const ch = (metric.value - prior.value) / Math.abs(prior.value);
    return { text: `${ch >= 0 ? "+" : ""}${(ch * 100).toFixed(0)}% vs ${prior.period}`, up: ch >= 0 };
  }
  const d = metric.value - prior.value;
  return { text: `${d >= 0 ? "+" : ""}${d.toFixed(1)} vs ${prior.period}`, up: d >= 0 };
}

/** KPI card. Pass `prior` (same metric, earlier period) to render a delta;
 *  set `higherIsBetter={false}` for metrics like net debt. */
export default function MetricCard({ metric, sub, prior, higherIsBetter = true }: {
  metric: Metric; sub?: string; prior?: Metric | null; higherIsBetter?: boolean;
}) {
  const delta = computeDelta(metric, prior);
  const good = delta ? delta.up === higherIsBetter : false;
  return (
    <div className="panel panel-hover p-4">
      <p className="subtle text-xs uppercase tracking-wide">{metric.label} <span className="normal-case">· {metric.period}</span></p>
      <p className={`mt-1 text-2xl font-semibold tabular-nums ${
        metric.value !== null && metric.value < 0 ? "text-[var(--neg)]" : "text-[var(--text)]"}`}>
        {formatBy(metric.value, metric.unit)}
      </p>
      {delta && (
        <p className={`mt-1 flex items-center gap-1 text-xs ${good ? "text-[var(--pos)]" : "text-[var(--neg)]"}`}>
          {delta.up ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
          {delta.text}
        </p>
      )}
      {sub && <p className="subtle mt-1 text-xs">{sub}</p>}
      {metric.caveat && (
        <p className="mt-2 flex items-start gap-1 text-xs text-[var(--warn)]">
          <Info className="mt-0.5 h-3 w-3 shrink-0" /> {metric.caveat}
        </p>
      )}
    </div>
  );
}
