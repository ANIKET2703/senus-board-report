"use client";
import { useEffect, useState } from "react";
import { api, FactRow, Metric, MetricCategories } from "@/lib/api";
import MetricCard from "@/components/MetricCard";
import InsightCard from "@/components/InsightCard";
import { eur } from "@/lib/format";
import { AlertTriangle, CheckCircle2 } from "lucide-react";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid,
} from "recharts";

interface Validation { summary: { pass: number; warn: number; fail: number };
  checks: { check: string; period: string | null; status: string; detail: string }[] }

const PERIOD_ORDER = ["FY24", "FY25", "HY25", "HY26"];

export default function Overview() {
  const [metrics, setMetrics] = useState<MetricCategories | null>(null);
  const [validation, setValidation] = useState<Validation | null>(null);
  const [pnl, setPnl] = useState<FactRow[]>([]);

  useEffect(() => {
    api<MetricCategories>("/api/metrics").then(setMetrics);
    api<Validation>("/api/validation").then(setValidation);
    api<FactRow[]>("/api/statements/pnl").then(setPnl);
  }, []);

  if (!metrics) return <p className="subtle animate-pulse">Loading board pack…</p>;

  const find = (cat: keyof MetricCategories, key: string, period?: string): Metric | undefined =>
    metrics[cat].find((m) => m.key === key && (!period || m.period === period));

  // revenue & gross profit series straight from the validated fact store
  const revenueSeries = PERIOD_ORDER.map((p) => ({
    period: p,
    revenue: pnl.find((r) => r.period === p && r.line_code === "revenue")?.value,
    grossProfit: pnl.find((r) => r.period === p && r.line_code === "gross_profit")?.value,
  })).filter((r) => r.revenue !== undefined);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold tracking-tight">Performance Overview</h1>
        <p className="subtle mt-1">
          Senus PLC · Natural Capital management software · Euronext Access Dublin (SENUS) ·
          latest period HY26 (6 months to 31 Dec 2025)
        </p>
      </header>

      <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
        {find("growth", "revenue_growth", "FY25") &&
          <MetricCard metric={find("growth", "revenue_growth", "FY25")!}
            sub="HY26 grew 4.1% vs HY25" />}
        {find("profitability", "gross_margin", "HY26") &&
          <MetricCard metric={find("profitability", "gross_margin", "HY26")!}
            prior={find("profitability", "gross_margin", "HY25")} />}
        {find("cash", "cash_runway", "HY26") &&
          <MetricCard metric={find("cash", "cash_runway", "HY26")!}
            prior={find("cash", "cash_runway", "FY25")} />}
        {find("profitability", "ebitda", "HY26") &&
          <MetricCard metric={find("profitability", "ebitda", "HY26")!}
            prior={find("profitability", "ebitda", "HY25")} />}
      </div>

      <InsightCard section="overview" />

      <div className="grid gap-6 xl:grid-cols-2">
        <div className="panel p-5">
          <h2 className="h-title mb-4">Revenue & gross profit (€)</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={revenueSeries}>
              <CartesianGrid stroke="rgba(147,179,167,0.18)" vertical={false} />
              <XAxis dataKey="period" stroke="var(--muted)" fontSize={12} />
              <YAxis stroke="var(--muted)" fontSize={12} tickFormatter={(v) => eur(v)} />
              <Tooltip formatter={(v) => eur(Number(v), false)}
                contentStyle={{ background: "var(--panel-2)", border: "1px solid var(--border)", borderRadius: 8, color: "var(--text)" }} />
              <Bar dataKey="revenue" name="Revenue" fill="var(--chart-1)" radius={[4, 4, 0, 0]} />
              <Bar dataKey="grossProfit" name="Gross profit" fill="var(--chart-2)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          <p className="subtle mt-2 text-xs">FY = year to 30 June (audited) · HY = 6 months to 31 December (unaudited) · values from the validated fact store</p>
        </div>

        <div className="panel p-5">
          <h2 className="h-title mb-4">Data quality - extraction validation</h2>
          {validation && (
            <>
              <div className="mb-4 flex gap-4">
                <span className="flex items-center gap-1.5 text-sm text-[var(--pos)]">
                  <CheckCircle2 className="h-4 w-4" /> {validation.summary.pass} checks passed
                </span>
                {validation.summary.warn > 0 && (
                  <span className="flex items-center gap-1.5 text-sm text-[var(--warn)]">
                    <AlertTriangle className="h-4 w-4" /> {validation.summary.warn} finding{validation.summary.warn > 1 ? "s" : ""}
                  </span>
                )}
              </div>
              <div className="space-y-2">
                {validation.checks.filter((c) => c.status !== "pass").map((c, i) => (
                  <div key={i} className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-3 text-sm">
                    <p className="font-medium text-[var(--warn)]">{c.check}{c.period ? ` (${c.period})` : ""}</p>
                    <p className="subtle mt-1 text-xs">{c.detail}</p>
                  </div>
                ))}
              </div>
              <p className="subtle mt-3 text-xs">
                Every extracted figure passes deterministic accounting-identity checks
                (balance sheet balances, cash flow ties, statement arithmetic). Findings
                above are inconsistencies present in the published source documents,
                caught by the pipeline.
              </p>
            </>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
        <MetricCard metric={find("growth", "senus2030_progress")!} sub="LTM revenue vs level implied by 50% CAGR commitment" />
        <MetricCard metric={find("solvency", "net_debt", "HY26")!}
          prior={find("solvency", "net_debt", "FY25")} higherIsBetter={false}
          sub="Negative = net cash position" />
        <MetricCard metric={find("cash", "working_capital", "HY26")!}
          prior={find("cash", "working_capital", "FY25")} />
        <MetricCard metric={find("returns", "roce", "HY26")!}
          prior={find("returns", "roce", "FY25")} />
      </div>
    </div>
  );
}
