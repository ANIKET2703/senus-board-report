"use client";
import { useEffect, useState } from "react";
import { api, FactRow, MetricCategories } from "@/lib/api";
import MetricCard from "@/components/MetricCard";
import ApiDown from "@/components/ApiDown";
import InsightCard from "@/components/InsightCard";
import ProvenanceTable from "@/components/ProvenanceTable";
import { eur } from "@/lib/format";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";

const MATURITY_BUCKETS: { code: string; bucket: string }[] = [
  { code: "debt_maturity_lt_1yr", bucket: "< 1 year" },
  { code: "debt_maturity_1_2yr", bucket: "1–2 years" },
  { code: "debt_maturity_2_5yr", bucket: "2–5 years" },
  { code: "debt_maturity_gt_5yr", bucket: "> 5 years" },
];

export default function Solvency() {
  const [metrics, setMetrics] = useState<MetricCategories | null>(null);
  const [bs, setBs] = useState<FactRow[]>([]);

  const [apiDown, setApiDown] = useState(false);
  useEffect(() => {
    api<MetricCategories>("/api/metrics").then(setMetrics).catch(() => setApiDown(true));
    api<FactRow[]>("/api/statements/bs").then(setBs).catch((e) => console.warn(e));
  }, []);
  if (apiDown) return <ApiDown />;
  if (!metrics) return <p className="subtle animate-pulse">Loading…</p>;

  // loan maturity straight from the fact store (ADF FS FY25 note 13, p.21) -
  // validated by the debt_maturity_sums_to_total accounting check
  const maturity = MATURITY_BUCKETS
    .map(({ code, bucket }) => ({
      bucket,
      amount: bs.find((r) => r.period === "FY25" && r.line_code === code)?.value,
    }))
    .filter((b): b is { bucket: string; amount: number } => b.amount !== undefined);
  const maturityTotal = maturity.reduce((s, b) => s + b.amount, 0);
  const cards = metrics.solvency.filter((m) => m.period === "FY25" || m.period === "HY26");

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold tracking-tight">Solvency & Leverage</h1>
        <p className="subtle mt-1">Bank debt €76.5k vs cash €735k at Dec-25 (net cash) · €100k SBCI term loan drawn FY25 · contingent consideration €850k (performance-linked, Loamin)</p>
      </header>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {cards.map((m) => <MetricCard key={m.key + m.period} metric={m} />)}
      </div>
      <InsightCard section="solvency" />
      <div className="grid gap-6 xl:grid-cols-2">
        <div className="panel p-5">
          <h2 className="h-title mb-4">
            Bank loan maturity profile{maturity.length > 0 && <> (FY25, {eur(maturityTotal, false)} total)</>}
          </h2>
          {maturity.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={maturity}>
                <CartesianGrid stroke="rgba(139,149,165,0.18)" vertical={false} />
                <XAxis dataKey="bucket" stroke="var(--muted)" fontSize={12} />
                <YAxis stroke="var(--muted)" fontSize={12} tickFormatter={(v) => eur(v)} />
                <Tooltip formatter={(v) => eur(Number(v), false)}
                  contentStyle={{ background: "var(--panel-2)", border: "1px solid var(--border)", borderRadius: 8, color: "var(--text)" }} />
                <Bar dataKey="amount" fill="var(--chart-1)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="subtle animate-pulse text-sm">Loading maturity facts…</p>
          )}
          <p className="subtle text-xs">Source: ADF FS FY25, note 13 (p.21), via the validated fact store (source-linked in the balance sheet below) · Directors&apos; loans of €133k additionally repayable (note 16)</p>
        </div>
        <div className="panel p-5">
          <h2 className="h-title mb-3">Credit considerations</h2>
          <ul className="space-y-3 text-sm">
            <li className="rounded-lg bg-[var(--panel-2)] p-3">
              <span className="font-medium text-[var(--pos)]">Net cash position at Dec-25.</span>{" "}
              <span className="subtle">Cash €735k comfortably exceeds bank debt €76.5k following the €1.1m raise.</span>
            </li>
            <li className="rounded-lg bg-[var(--panel-2)] p-3">
              <span className="font-medium text-[var(--warn)]">Negative EBITDA means debt service is equity-funded.</span>{" "}
              <span className="subtle">DSCR is not meaningful in its textbook form until the FY2028 EBITDA-positive target; runway is the more meaningful measure at this stage. At HY dates scheduled principal isn&apos;t disclosed, so the ratio is suppressed rather than computed interest-only.</span>
            </li>
            <li className="rounded-lg bg-[var(--panel-2)] p-3">
              <span className="font-medium text-[var(--warn)]">€850k contingent consideration (Loamin).</span>{" "}
              <span className="subtle">Performance-linked; no cash paid at completion. A future call on cash if targets are met.</span>
            </li>
            <li className="rounded-lg bg-[var(--panel-2)] p-3">
              <span className="font-medium text-[var(--pos)]">FY25 net liabilities restored to positive equity at HY26.</span>{" "}
              <span className="subtle">Net assets €561k at Dec-25 after listing reorganisation and raise.</span>
            </li>
          </ul>
        </div>
      </div>
      <div>
        <h2 className="h-title mb-3">Consolidated balance sheet</h2>
        <ProvenanceTable rows={bs} periods={["FY24", "FY25", "HY25", "HY26"]} />
      </div>
    </div>
  );
}
