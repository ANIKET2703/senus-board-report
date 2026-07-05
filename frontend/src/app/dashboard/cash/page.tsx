"use client";
import { useEffect, useState } from "react";
import { api, FactRow, MetricCategories } from "@/lib/api";
import MetricCard from "@/components/MetricCard";
import InsightCard from "@/components/InsightCard";
import ProvenanceTable from "@/components/ProvenanceTable";
import { eur } from "@/lib/format";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell, ReferenceLine,
} from "recharts";

interface Bridge { period: string; steps: { label: string; value: number }[]; fcf: number }

export default function Cash() {
  const [metrics, setMetrics] = useState<MetricCategories | null>(null);
  const [bridge, setBridge] = useState<Bridge | null>(null);
  const [cf, setCf] = useState<FactRow[]>([]);
  const [period, setPeriod] = useState("FY25");

  useEffect(() => {
    api<MetricCategories>("/api/metrics").then(setMetrics);
    api<FactRow[]>("/api/statements/cf").then(setCf);
  }, []);
  useEffect(() => { api<Bridge>(`/api/metrics/fcf-bridge/${period}`).then(setBridge); }, [period]);
  if (!metrics) return <p className="subtle animate-pulse">Loading…</p>;

  // waterfall: cumulative offsets
  let running = 0;
  const waterfall = bridge ? [
    ...bridge.steps.map((s) => {
      const bar = { name: s.label, value: s.value, offset: s.value >= 0 ? running : running + s.value };
      running += s.value;
      return bar;
    }),
    { name: "FCF", value: bridge.fcf, offset: bridge.fcf >= 0 ? 0 : bridge.fcf },
  ] : [];

  const cards = metrics.cash.filter((m) => m.period === "HY26" || (m.key === "cash_runway"));

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold tracking-tight">Cash & Liquidity</h1>
        <p className="subtle mt-1">HY26 closing cash €735k after €1.1m equity raise · pre-financing burn ≈ €70k/month</p>
      </header>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map((m) => <MetricCard key={m.key + m.period} metric={m} />)}
      </div>
      <InsightCard section="cash" />
      <div className="panel p-5">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="h-title">EBITDA → Free Cash Flow bridge</h2>
          <select value={period} onChange={(e) => setPeriod(e.target.value)}
            className="rounded-lg border border-[var(--border)] bg-[var(--panel-2)] px-2 py-1 text-sm outline-none">
            {["FY24", "FY25", "HY25", "HY26"].map((p) => <option key={p}>{p}</option>)}
          </select>
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={waterfall}>
            <CartesianGrid stroke="rgba(139,149,165,0.18)" vertical={false} />
            <XAxis dataKey="name" stroke="#8b95a5" fontSize={11} interval={0} angle={-15} textAnchor="end" height={60} />
            <YAxis stroke="#8b95a5" fontSize={12} tickFormatter={(v) => eur(v)} />
            <ReferenceLine y={0} stroke="rgba(139,149,165,0.45)" />
            <Tooltip formatter={(v) => eur(Number(v), false)}
              contentStyle={{ background: "var(--panel-2)", border: "1px solid var(--border)", borderRadius: 8, color: "var(--text)" }} />
            <Bar dataKey="offset" stackId="w" fill="transparent" />
            <Bar dataKey="value" stackId="w" radius={[4, 4, 0, 0]}>
              {waterfall.map((s, i) => (
                <Cell key={i} fill={s.name === "FCF" ? "var(--chart-1)" : s.value >= 0 ? "var(--pos)" : "var(--neg)"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        {bridge && <p className="subtle mt-2 text-xs">
          {period} free cash flow: <span className="font-medium">{eur(bridge.fcf, false)}</span> (operating + investing, pre-financing - the measure a credit provider uses for debt service capacity)
        </p>}
      </div>
      <div>
        <h2 className="h-title mb-3">Consolidated cash flow - hover any figure for provenance</h2>
        <ProvenanceTable rows={cf} periods={["FY24", "FY25", "HY25", "HY26"]} />
      </div>
    </div>
  );
}
