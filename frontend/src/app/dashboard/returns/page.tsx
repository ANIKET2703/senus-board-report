"use client";
import { useEffect, useState } from "react";
import { api, MetricCategories } from "@/lib/api";
import MetricCard from "@/components/MetricCard";
import ApiDown from "@/components/ApiDown";
import InsightCard from "@/components/InsightCard";
import { eur } from "@/lib/format";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, ReferenceLine } from "recharts";

export default function Returns() {
  const [metrics, setMetrics] = useState<MetricCategories | null>(null);
  const [apiDown, setApiDown] = useState(false);
  useEffect(() => {
    api<MetricCategories>("/api/metrics").then(setMetrics).catch(() => setApiDown(true));
  }, []);
  if (apiDown) return <ApiDown />;
  if (!metrics) return <p className="subtle animate-pulse">Loading…</p>;

  const roces = metrics.returns.filter((m) => m.key === "roce");
  const rpe = metrics.returns.filter((m) => m.key === "revenue_per_employee");
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold tracking-tight">Returns</h1>
        <p className="subtle mt-1">Capital efficiency during the investment phase - trend matters more than level pre-breakeven</p>
      </header>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {roces.filter((m) => m.period === "FY25" || m.period === "HY26").map((m) => (
          <MetricCard key={m.period} metric={m}
            prior={m.period === "HY26" ? roces.find((p) => p.period === "FY25") : undefined} />
        ))}
        {rpe.filter((m) => m.period === "FY24" || m.period === "FY25").map((m) => (
          <MetricCard key={m.period} metric={m}
            prior={m.period === "FY25" ? rpe.find((p) => p.period === "FY24") : undefined}
            sub={m.period === "FY25"
              ? "18 avg employees (19 in FY24) - revenue up 21.6% with a smaller team"
              : `${m.inputs.employees} avg employees`} />
        ))}
      </div>
      <InsightCard section="returns" />
      <div className="panel p-5">
        <h2 className="h-title mb-4">Revenue per employee (€)</h2>
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={rpe.filter((m) => m.value !== null).map((m) => ({ period: m.period, value: m.value }))}>
            <CartesianGrid stroke="rgba(139,149,165,0.18)" vertical={false} />
            <XAxis dataKey="period" stroke="var(--muted)" fontSize={12} />
            <YAxis stroke="var(--muted)" fontSize={12} tickFormatter={(v) => eur(v)} />
            <ReferenceLine y={0} stroke="rgba(139,149,165,0.45)" />
            <Tooltip formatter={(v) => eur(Number(v), false)}
              contentStyle={{ background: "var(--panel-2)", border: "1px solid var(--border)", borderRadius: 8, color: "var(--text)" }} />
            <Bar dataKey="value" fill="var(--chart-2)" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
        <p className="subtle mt-2 text-xs">
          Productivity improved ~28% YoY (€36.2k → €46.5k per head). AI-enabled productivity is an explicit
          plank of the Loamin integration strategy. Headcount is disclosed in the audited FY accounts only.
        </p>
      </div>
    </div>
  );
}
