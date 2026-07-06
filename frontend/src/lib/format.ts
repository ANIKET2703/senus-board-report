export const eur = (v: number | null | undefined, compact = true): string => {
  if (v === null || v === undefined) return "-";
  const abs = Math.abs(v);
  if (compact && abs >= 1_000_000) return `€${(v / 1_000_000).toFixed(2)}m`;
  if (compact && abs >= 10_000) return `€${(v / 1_000).toFixed(0)}k`;
  // small non-integer values (e.g. a €6.15 share price) keep their cents
  if (abs > 0 && abs < 1_000 && !Number.isInteger(v))
    return `€${v.toLocaleString("en-IE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  return `€${v.toLocaleString("en-IE", { maximumFractionDigits: 0 })}`;
};
export const pct = (v: number | null | undefined, dp = 1): string =>
  v === null || v === undefined ? "-" : `${(v * 100).toFixed(dp)}%`;
export const ratio = (v: number | null | undefined, dp = 2): string =>
  v === null || v === undefined ? "-" : `${v.toFixed(dp)}x`;
export const months = (v: number | null | undefined): string =>
  v === null || v === undefined ? "-" : `${v.toFixed(1)} months`;
export const formatBy = (v: number | null, unit: string): string =>
  unit === "pct" ? pct(v) : unit === "x" || unit === "ratio" ? ratio(v)
  : unit === "months" ? months(v) : unit === "count" ? (v ?? "-").toString() : eur(v);
