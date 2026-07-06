"use client";
import { useEffect, useState } from "react";
import { api, Metric } from "@/lib/api";
import MetricCard from "@/components/MetricCard";
import ApiDown from "@/components/ApiDown";
import InsightCard from "@/components/InsightCard";
import { eur, pct } from "@/lib/format";
import { Info } from "lucide-react";
import {
  ResponsiveContainer, ComposedChart, Bar, Line, XAxis, YAxis, Tooltip,
  CartesianGrid, Legend, ReferenceLine,
} from "recharts";

interface Valuation {
  available: boolean;
  reason?: string;
  as_of: string | null;
  share_price: number;
  price_52w_high: number | null;
  price_52w_low: number | null;
  admission_price: number | null;
  price_vs_admission: number | null;
  shares_in_issue: number;
  market_cap: number;
  net_debt: number;
  enterprise_value: number;
  ltm_revenue: number;
  ev_ltm_revenue: number | null;
  guidance_path: { year: string; revenue: number; implied_ev_revenue: number }[];
  caveats: string[];
}

const card = (key: string, label: string, value: number | null, unit: string,
  period: string, caveat: string | null = null): Metric =>
  ({ key, label, value, unit, period, caveat, inputs: {} });

export default function ValuationPage() {
  const [v, setV] = useState<Valuation | null>(null);
  const [apiDown, setApiDown] = useState(false);
  useEffect(() => {
    api<Valuation>("/api/valuation").then(setV).catch(() => setApiDown(true));
  }, []);
  if (apiDown) return <ApiDown />;
  if (!v) return <p className="subtle animate-pulse">Loading valuation…</p>;
  if (!v.available) return <p className="subtle">{v.reason ?? "Valuation unavailable."}</p>;

  const asOf = v.as_of
    ? new Date(v.as_of).toLocaleDateString("en-IE", { day: "numeric", month: "short", year: "2-digit" })
    : "latest";
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold tracking-tight">Valuation & Market</h1>
        <p className="subtle mt-1">
          SENUS · Euronext Access Dublin · admitted 22 Dec 2025 at €{v.admission_price} ·
          what the market pays today vs what the Senus 2030 commitment implies
        </p>
      </header>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard metric={card("share_price", "Share price", v.share_price, "EUR", asOf)}
          sub={`52w ${eur(v.price_52w_low, false)}–${eur(v.price_52w_high, false)} · ${
            v.price_vs_admission !== null ? `${v.price_vs_admission >= 0 ? "+" : ""}${pct(v.price_vs_admission)} since admission` : ""}`} />
        <MetricCard metric={card("market_cap", "Market capitalisation", v.market_cap, "EUR", asOf)}
          sub={`${v.shares_in_issue.toLocaleString("en-IE")} shares in issue (unchanged since admission)`} />
        <MetricCard metric={card("ev", "Enterprise value", v.enterprise_value, "EUR", asOf)}
          sub={`Market cap ${v.net_debt < 0 ? "less net cash" : "plus net debt"} of ${eur(Math.abs(v.net_debt))} (HY26 balance sheet)`} />
        <MetricCard metric={card("ev_ltm", "EV / LTM revenue", v.ev_ltm_revenue, "x", asOf)}
          sub={`LTM revenue to Dec-25: ${eur(v.ltm_revenue, false)}`} />
      </div>

      <InsightCard section="valuation" />

      <div className="panel p-5">
        <h2 className="h-title mb-4">Multiple compression if Senus 2030 is delivered (EV held at today&apos;s {eur(v.enterprise_value)})</h2>
        <ResponsiveContainer width="100%" height={280}>
          <ComposedChart data={v.guidance_path}>
            <CartesianGrid stroke="rgba(139,149,165,0.18)" vertical={false} />
            <XAxis dataKey="year" stroke="var(--muted)" fontSize={12} />
            <YAxis yAxisId="rev" stroke="var(--muted)" fontSize={12} tickFormatter={(x) => eur(x)} />
            <YAxis yAxisId="mult" orientation="right" stroke="var(--muted)" fontSize={12} tickFormatter={(x) => `${x}x`} />
            <ReferenceLine yAxisId="mult" y={10} stroke="rgba(139,149,165,0.45)" strokeDasharray="4 4" />
            <Tooltip
              formatter={(val, name) => name === "EV / revenue" ? `${Number(val).toFixed(2)}x` : eur(Number(val), false)}
              contentStyle={{ background: "var(--panel-2)", border: "1px solid var(--border)", borderRadius: 8, color: "var(--text)" }} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Bar yAxisId="rev" dataKey="revenue" name="Guidance-path revenue" fill="var(--chart-1)" radius={[4, 4, 0, 0]} />
            <Line yAxisId="mult" type="monotone" dataKey="implied_ev_revenue" name="EV / revenue" stroke="var(--chart-2)" strokeWidth={2} dot />
          </ComposedChart>
        </ResponsiveContainer>
        <p className="subtle mt-2 text-xs">
          Revenue path = the published ≥50% CAGR commitment from the FY25 base (assumptions are adjustable on the
          Senus 2030 page). Today&apos;s {v.ev_ltm_revenue}x LTM multiple compresses to{" "}
          {v.guidance_path[v.guidance_path.length - 1]?.implied_ev_revenue}x by FY30 - the market is
          pricing in delivery of the growth plan, not the current P&amp;L.
        </p>
      </div>

      <div className="panel p-5">
        <h2 className="h-title mb-3">Basis &amp; limitations</h2>
        <ul className="space-y-3 text-sm">
          {v.caveats.map((c) => (
            <li key={c.slice(0, 40)} className="flex items-start gap-2 rounded-lg bg-[var(--panel-2)] p-3">
              <Info className="mt-0.5 h-4 w-4 shrink-0 text-[var(--warn)]" />
              <span className="subtle">{c}</span>
            </li>
          ))}
        </ul>
        <p className="subtle mt-3 text-xs">
          Every input on this page is a fact-store value with provenance: shares and admission price from the
          Direct Listing press release (p.3), prices from the Euronext market-data exports (Documents &amp; Audit),
          net debt from the HY26 balance sheet. Cross-checks: shares × admission price ties to the disclosed
          €13.13m admission market cap; the 52-week move ties to close ÷ admission price.
        </p>
      </div>
    </div>
  );
}
