"use client";
import { useEffect, useState } from "react";
import { api, FactRow, Metric, MetricCategories } from "@/lib/api";
import MetricCard from "@/components/MetricCard";
import InsightCard from "@/components/InsightCard";
import { eur } from "@/lib/format";
import {
  ResponsiveContainer, PieChart, Pie, Cell, Legend, Tooltip,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from "recharts";

const COLORS = ["var(--chart-1)", "var(--chart-2)", "var(--chart-3)"];

export default function Growth() {
  const [metrics, setMetrics] = useState<MetricCategories | null>(null);
  const [kpis, setKpis] = useState<FactRow[]>([]);

  useEffect(() => {
    api<MetricCategories>("/api/metrics").then(setMetrics);
    api<FactRow[]>("/api/statements/kpi").then(setKpis);
  }, []);
  if (!metrics) return <p className="subtle animate-pulse">Loading…</p>;

  const k = (code: string) => kpis.find((x) => x.line_code === code)?.value;
  const channelMix = [
    { name: `Enterprise (${k("customers_enterprise") ?? "-"} customers)`, value: k("revenue_mix_enterprise") ?? 0 },
    { name: `R&D (${k("customers_rnd") ?? "-"} customers)`, value: k("revenue_mix_rnd") ?? 0 },
    { name: `Independent (${k("customers_independent") ?? "-"} customers)`, value: k("revenue_mix_independent") ?? 0 },
  ];
  const acv = [
    { product: "Senus SOIL", acv: k("acv_soil") ?? 0 },
    { product: "Senus TERRAIN", acv: k("acv_terrain") ?? 0 },
    { product: "Senus ERA", acv: k("acv_era") ?? 0 },
  ];

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold tracking-tight">Growth & Revenue</h1>
        <p className="subtle mt-1">FY25 revenue €836,991 across 138 customer accounts · Senus 2030 targets ≥50% CAGR</p>
      </header>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.growth.map((m: Metric) => <MetricCard key={m.key + m.period} metric={m} />)}
        <MetricCard metric={{ key: "bookings", label: "Bookings (deals closed)",
          value: k("deals_closed_value") ?? null, unit: "EUR", period: "HY26", caveat: null, inputs: {} }}
          sub={`${eur(k("deals_closed_value") ?? null)} closed across ${k("deals_closed_customers") ?? "-"} enterprise customers · ${eur(k("open_pipeline_value") ?? null)} open pipeline`} />
      </div>
      <p className="subtle text-xs">
        No monthly (MoM) view: Senus publishes FY and half-year figures only - recorded as a
        disclosure-coverage finding in Data quality.
      </p>
      <InsightCard section="growth" />
      <div className="grid gap-6 xl:grid-cols-2">
        <div className="panel p-5">
          <h2 className="h-title mb-2">FY25 revenue mix by channel</h2>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={channelMix} dataKey="value" nameKey="name" innerRadius={55} outerRadius={90} paddingAngle={2}>
                {channelMix.map((_, i) => <Cell key={i} fill={COLORS[i]} stroke="none" />)}
              </Pie>
              <Tooltip formatter={(v) => `${(Number(v) * 100).toFixed(0)}%`}
                contentStyle={{ background: "var(--panel-2)", border: "1px solid var(--border)", borderRadius: 8, color: "var(--text)" }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
            </PieChart>
          </ResponsiveContainer>
          <p className="subtle text-xs">Source: Information Document p.11 · ~78% of FY25 revenue from Ireland, active in 11 jurisdictions</p>
        </div>
        <div className="panel p-5">
          <h2 className="h-title mb-2">Average Enterprise contract value by product (FY25)</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={acv} layout="vertical">
              <CartesianGrid stroke="rgba(139,149,165,0.18)" horizontal={false} />
              <XAxis type="number" stroke="#8b95a5" fontSize={12} tickFormatter={(v) => eur(v)} />
              <YAxis type="category" dataKey="product" stroke="#8b95a5" fontSize={12} width={110} />
              <Tooltip formatter={(v) => eur(Number(v), false)}
                contentStyle={{ background: "var(--panel-2)", border: "1px solid var(--border)", borderRadius: 8, color: "var(--text)" }} />
              <Bar dataKey="acv" fill="var(--chart-1)" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
          <p className="subtle text-xs">FY30 target: Enterprise ACV &gt; €50,000 · &gt;100 Enterprise customers</p>
        </div>
      </div>
    </div>
  );
}
