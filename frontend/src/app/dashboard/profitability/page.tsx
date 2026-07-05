"use client";
import { useEffect, useState } from "react";
import { api, FactRow, MetricCategories } from "@/lib/api";
import MetricCard from "@/components/MetricCard";
import InsightCard from "@/components/InsightCard";
import ProvenanceTable from "@/components/ProvenanceTable";
import { pct } from "@/lib/format";
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, Legend,
} from "recharts";

export default function Profitability() {
  const [metrics, setMetrics] = useState<MetricCategories | null>(null);
  const [pnl, setPnl] = useState<FactRow[]>([]);

  useEffect(() => {
    api<MetricCategories>("/api/metrics").then(setMetrics);
    api<FactRow[]>("/api/statements/pnl").then(setPnl);
  }, []);
  if (!metrics) return <p className="subtle animate-pulse">Loading…</p>;

  const series = ["FY24", "FY25", "HY25", "HY26"].map((p) => ({
    period: p,
    gross: metrics.profitability.find((m) => m.key === "gross_margin" && m.period === p)?.value,
    operating: metrics.profitability.find((m) => m.key === "operating_margin" && m.period === p)?.value,
    ebitda: metrics.profitability.find((m) => m.key === "ebitda_margin" && m.period === p)?.value,
  }));

  const pm = (key: string, period: string) =>
    metrics.profitability.find((m) => m.key === key && m.period === period);
  // latest period first, each with its prior-period delta; 3 columns x 2 rows (no orphan cards)
  const cardRows: { period: string; prior: string }[] = [
    { period: "HY26", prior: "HY25" },
    { period: "FY25", prior: "FY24" },
  ];

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold tracking-tight">Profitability</h1>
        <p className="subtle mt-1">Gross margin expanded 62.8% → 77.5% (FY) and 79.8% → 81.7% (HY) · EBITDA-positive guidance: FY2028</p>
      </header>
      <div className="grid grid-cols-2 gap-4 xl:grid-cols-3">
        {cardRows.flatMap(({ period, prior }) =>
          ["gross_margin", "ebitda", "ebitda_margin"].map((key) => {
            const m = pm(key, period);
            return m ? <MetricCard key={key + period} metric={m} prior={pm(key, prior)} /> : null;
          }))}
      </div>
      <InsightCard section="profitability" />
      <div className="panel p-5">
        <h2 className="h-title mb-4">Margin trend</h2>
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={series}>
            <CartesianGrid stroke="rgba(139,149,165,0.18)" vertical={false} />
            <XAxis dataKey="period" stroke="#8b95a5" fontSize={12} />
            <YAxis stroke="#8b95a5" fontSize={12} tickFormatter={(v) => pct(v, 0)} />
            <Tooltip formatter={(v) => pct(Number(v))}
              contentStyle={{ background: "var(--panel-2)", border: "1px solid var(--border)", borderRadius: 8, color: "var(--text)" }} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Line type="monotone" dataKey="gross" name="Gross margin" stroke="var(--chart-2)" strokeWidth={2} dot />
            <Line type="monotone" dataKey="operating" name="Operating margin" stroke="var(--chart-1)" strokeWidth={2} dot />
            <Line type="monotone" dataKey="ebitda" name="EBITDA margin" stroke="var(--chart-3)" strokeWidth={2} dot />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div>
        <h2 className="h-title mb-3">Consolidated P&L - hover any figure for source provenance</h2>
        <ProvenanceTable rows={pnl} periods={["FY24", "FY25", "HY25", "HY26"]} />
      </div>
    </div>
  );
}
