"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import InsightCard from "@/components/InsightCard";
import { eur, pct } from "@/lib/format";
import {
  ResponsiveContainer, ComposedChart, Bar, Line, XAxis, YAxis, Tooltip, CartesianGrid, Legend, ReferenceLine,
} from "recharts";

interface Scenario {
  assumptions: Record<string, number | string>;
  projection: { year: string; revenue: number; gross_profit: number; opex: number; ebitda: number; ebitda_margin: number | null }[];
  ebitda_breakeven_year: string | null;
  guidance_breakeven_year: string;
}

export default function ScenarioPage() {
  const [growth, setGrowth] = useState(0.5);
  const [grossMargin, setGrossMargin] = useState(0.7748);
  const [opexGrowth, setOpexGrowth] = useState(0.18);
  const [data, setData] = useState<Scenario | null>(null);

  useEffect(() => {
    const t = setTimeout(() => {
      api<Scenario>(`/api/scenario?growth=${growth}&gross_margin=${grossMargin}&opex_growth=${opexGrowth}`)
        .then(setData);
    }, 250);
    return () => clearTimeout(t);
  }, [growth, grossMargin, opexGrowth]);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold tracking-tight">Senus 2030 - Scenario Model</h1>
        <p className="subtle mt-1">
          Company commitments: revenue CAGR ≥ 50% (base FY25 €837k) · EBITDA-positive during FY2028 ·
          &gt;100 Enterprise customers · Ireland &lt; 50% of revenue
        </p>
      </header>
      <div className="panel grid gap-6 p-5 md:grid-cols-3">
        {[
          { label: `Revenue CAGR: ${pct(growth, 0)}`, value: growth, set: setGrowth, min: 0, max: 1, step: 0.05, hint: "Guidance: ≥50%" },
          { label: `Gross margin: ${pct(grossMargin, 1)}`, value: grossMargin, set: setGrossMargin, min: 0.5, max: 0.95, step: 0.005, hint: "FY25 actual: 77.5%" },
          { label: `Opex growth: ${pct(opexGrowth, 0)}`, value: opexGrowth, set: setOpexGrowth, min: 0, max: 0.6, step: 0.02, hint: "vs FY25 opex €1.29m" },
        ].map((s) => (
          <div key={s.label}>
            <label className="mb-1 block text-sm font-medium">{s.label}</label>
            <input type="range" min={s.min} max={s.max} step={s.step} value={s.value}
              onChange={(e) => s.set(Number(e.target.value))} className="w-full accent-[var(--accent)]" />
            <p className="subtle text-xs">{s.hint}</p>
          </div>
        ))}
      </div>

      {data && (
        <>
          <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
            <div className="panel p-4">
              <p className="subtle">FY30 revenue</p>
              <p className="mt-1 text-2xl font-semibold">{eur(data.projection[4].revenue)}</p>
            </div>
            <div className="panel p-4">
              <p className="subtle">FY30 EBITDA</p>
              <p className={`mt-1 text-2xl font-semibold ${data.projection[4].ebitda < 0 ? "text-[var(--neg)]" : "text-[var(--pos)]"}`}>
                {eur(data.projection[4].ebitda)}</p>
            </div>
            <div className="panel p-4">
              <p className="subtle">Modelled EBITDA breakeven</p>
              <p className="mt-1 text-2xl font-semibold">{data.ebitda_breakeven_year ?? "not reached"}</p>
            </div>
            <div className="panel p-4">
              <p className="subtle">Company guidance</p>
              <p className="mt-1 text-2xl font-semibold">{data.guidance_breakeven_year}</p>
              {data.ebitda_breakeven_year && data.ebitda_breakeven_year <= data.guidance_breakeven_year
                ? <p className="text-xs text-[var(--pos)]">Scenario meets guidance</p>
                : <p className="text-xs text-[var(--warn)]">Scenario misses guidance</p>}
            </div>
          </div>
          <InsightCard section="outlook" />
          <div className="panel p-5">
            <h2 className="h-title mb-4">Projection FY26–FY30</h2>
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={data.projection}>
                <CartesianGrid stroke="rgba(139,149,165,0.18)" vertical={false} />
                <XAxis dataKey="year" stroke="#8b95a5" fontSize={12} />
                <YAxis stroke="#8b95a5" fontSize={12} tickFormatter={(v) => eur(v)} />
                <ReferenceLine y={0} stroke="rgba(139,149,165,0.45)" />
                <Tooltip formatter={(v) => eur(Number(v), false)}
                  contentStyle={{ background: "var(--panel-2)", border: "1px solid var(--border)", borderRadius: 8, color: "var(--text)" }} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Bar dataKey="revenue" name="Revenue" fill="var(--chart-1)" radius={[4, 4, 0, 0]} />
                <Line type="monotone" dataKey="ebitda" name="EBITDA" stroke="var(--chart-2)" strokeWidth={2} dot />
              </ComposedChart>
            </ResponsiveContainer>
            <p className="subtle mt-2 text-xs">
              Assumptions are explicit and adjustable - the model never hides its inputs. HY26 actual growth (4.1% YoY)
              is materially below the 50% trajectory; large enterprise/state contracts (e.g. €300k Biochar award) are
              expected to be lumpy rather than linear.
            </p>
          </div>
        </>
      )}
    </div>
  );
}
