"use client";
import { createContext, useContext, useEffect, useState } from "react";

export const PERIODS = ["FY24", "FY25", "HY25", "HY26"] as const;
export type ReportPeriod = (typeof PERIODS)[number];

const Ctx = createContext<{ period: ReportPeriod; setPeriod: (p: ReportPeriod) => void }>({
  period: "HY26", setPeriod: () => {},
});

export function PeriodProvider({ children }: { children: React.ReactNode }) {
  const [period, setPeriod] = useState<ReportPeriod>("HY26");
  useEffect(() => {
    const saved = localStorage.getItem("period");
    if (saved && (PERIODS as readonly string[]).includes(saved)) setPeriod(saved as ReportPeriod);
  }, []);
  const set = (p: ReportPeriod) => { setPeriod(p); localStorage.setItem("period", p); };
  return <Ctx.Provider value={{ period, setPeriod: set }}>{children}</Ctx.Provider>;
}
export const usePeriod = () => useContext(Ctx);
