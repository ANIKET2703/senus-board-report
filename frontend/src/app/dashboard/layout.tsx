"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { AudienceProvider, AUDIENCES, useAudience } from "@/lib/audience";
import { PeriodProvider, PERIODS, usePeriod, type ReportPeriod } from "@/lib/period";
import { api, getToken } from "@/lib/api";
import {
  LayoutDashboard, TrendingUp, PieChart, Droplets, Scale, RotateCcw,
  Target, FileText, MessageSquare, LogOut, ShieldCheck, Sun, Moon,
  AlertTriangle, Printer, Menu,
} from "lucide-react";
import { useTheme } from "@/lib/theme";

const NAV = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/dashboard/growth", label: "Growth & Revenue", icon: TrendingUp },
  { href: "/dashboard/profitability", label: "Profitability", icon: PieChart },
  { href: "/dashboard/cash", label: "Cash & Liquidity", icon: Droplets },
  { href: "/dashboard/solvency", label: "Solvency & Leverage", icon: Scale },
  { href: "/dashboard/returns", label: "Returns", icon: RotateCcw },
  { href: "/dashboard/scenario", label: "Senus 2030", icon: Target },
  { href: "/dashboard/documents", label: "Documents & Audit", icon: FileText },
  { href: "/dashboard/chat", label: "Ask the Board Pack", icon: MessageSquare },
];

// credit providers see solvency first; investors see growth + scenario first
const ORDER: Record<string, string[]> = {
  credit: ["/dashboard", "/dashboard/solvency", "/dashboard/cash", "/dashboard/profitability",
           "/dashboard/growth", "/dashboard/returns", "/dashboard/scenario", "/dashboard/documents", "/dashboard/chat"],
  investor: ["/dashboard", "/dashboard/growth", "/dashboard/scenario", "/dashboard/profitability",
             "/dashboard/cash", "/dashboard/returns", "/dashboard/solvency", "/dashboard/documents", "/dashboard/chat"],
};

function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const router = useRouter();
  const { audience } = useAudience();
  const nav = ORDER[audience]
    ? ORDER[audience].map((h) => NAV.find((n) => n.href === h)!)
    : NAV;

  return (
    <aside className="flex h-full w-64 shrink-0 flex-col overflow-y-auto border-r border-[var(--border)] bg-[var(--panel)] p-4">
      <Link href="/dashboard" onClick={onNavigate} title="Go to overview"
        className="mb-6 flex items-center gap-2 rounded-lg px-2 py-1 transition-colors hover:bg-[var(--panel-2)]">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--accent)] font-bold text-white">S</div>
        <div className="flex-1">
          <p className="font-semibold leading-tight">Senus PLC</p>
          <p className="text-xs text-[var(--muted)]">Board Report</p>
        </div>
      </Link>

      <nav className="flex-1 space-y-1">
        {nav.map(({ href, label, icon: Icon }) => (
          <Link key={href} href={href} onClick={onNavigate}
            className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
              pathname === href ? "bg-[var(--accent)] text-white" : "text-[var(--muted)] hover:bg-[var(--panel-2)] hover:text-[var(--text)]"}`}>
            <Icon className="h-4 w-4" /> {label}
          </Link>
        ))}
      </nav>

      <div className="mt-4 space-y-2 border-t border-[var(--border)] pt-4">
        <p className="flex items-center gap-2 px-3 text-xs text-[var(--muted)]">
          <ShieldCheck className="h-3.5 w-3.5 text-[var(--pos)]" />
          All figures traceable to source filings
        </p>
        <button onClick={() => { localStorage.removeItem("token"); router.push("/login"); }}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-[var(--muted)] hover:bg-[var(--panel-2)]">
          <LogOut className="h-4 w-4" /> Sign out
        </button>
      </div>
    </aside>
  );
}

interface ValidationSummary { summary: { pass: number; warn: number; fail: number } }

function TopBar({ onMenu }: { onMenu: () => void }) {
  const { audience, setAudience } = useAudience();
  const { period, setPeriod } = usePeriod();
  const { theme, toggle } = useTheme();
  const [checks, setChecks] = useState<ValidationSummary["summary"] | null>(null);

  useEffect(() => {
    api<ValidationSummary>("/api/validation").then((v) => setChecks(v.summary)).catch(() => {});
  }, []);

  const selectCls =
    "rounded-lg border border-[var(--border)] bg-[var(--panel-2)] px-2 py-1.5 text-sm outline-none";
  return (
    <div className="no-print sticky top-0 z-10 flex flex-wrap items-center gap-x-3 gap-y-2 border-b border-[var(--border)] bg-[var(--panel)] px-4 py-3 md:px-6">
      <button onClick={onMenu} aria-label="Open menu"
        className="rounded-lg border border-[var(--border)] p-2 text-[var(--muted)] lg:hidden">
        <Menu className="h-4 w-4" />
      </button>
      <label className="hidden text-xs uppercase tracking-wide text-[var(--muted)] sm:block">Viewing as</label>
      <select value={audience} onChange={(e) => setAudience(e.target.value as never)} className={selectCls}>
        {AUDIENCES.map((a) => <option key={a.id} value={a.id}>{a.label}</option>)}
      </select>
      <label className="hidden text-xs uppercase tracking-wide text-[var(--muted)] sm:block">Period</label>
      <select value={period} onChange={(e) => setPeriod(e.target.value as ReportPeriod)} className={selectCls}>
        {PERIODS.map((p) => <option key={p}>{p}</option>)}
      </select>

      {checks && (
        <Link href="/dashboard/documents" title="Deterministic accounting-identity checks on every extracted figure"
          className="hidden items-center gap-1.5 rounded-lg bg-[var(--panel-2)] px-2.5 py-1.5 text-xs text-[var(--muted)] hover:text-[var(--text)] md:flex">
          <ShieldCheck className="h-3.5 w-3.5 text-[var(--pos)]" /> {checks.pass} checks passed
          {checks.warn > 0 && (
            <span className="flex items-center gap-1 text-[var(--warn)]">
              · <AlertTriangle className="h-3 w-3" /> {checks.warn} finding{checks.warn > 1 ? "s" : ""}
            </span>
          )}
        </Link>
      )}

      <div className="ml-auto flex items-center gap-2">
        <button onClick={() => window.print()}
          className="hidden items-center gap-2 rounded-lg border border-[var(--border)] px-3 py-1.5 text-sm text-[var(--muted)] transition-colors hover:border-[var(--accent)] hover:text-[var(--text)] sm:flex">
          <Printer className="h-4 w-4" /> Export pack
        </button>
        <button onClick={toggle} title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          className="rounded-lg border border-[var(--border)] p-2 text-[var(--muted)] transition-colors hover:border-[var(--muted)] hover:text-[var(--text)]">
          {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </button>
      </div>
    </div>
  );
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  useEffect(() => {
    if (!getToken()) router.replace("/login");
    else setReady(true);
  }, [router]);
  if (!ready) return null;
  return (
    <AudienceProvider>
      <PeriodProvider>
        <div className="flex min-h-screen">
          <div className="sticky top-0 hidden h-screen lg:block">
            <Sidebar />
          </div>
          {menuOpen && (
            <div className="fixed inset-0 z-40 lg:hidden">
              <div className="absolute inset-0 bg-black/50" onClick={() => setMenuOpen(false)} />
              <div className="absolute inset-y-0 left-0">
                <Sidebar onNavigate={() => setMenuOpen(false)} />
              </div>
            </div>
          )}
          <div className="flex min-w-0 flex-1 flex-col">
            <TopBar onMenu={() => setMenuOpen(true)} />
            <main className="mx-auto w-full max-w-[1240px] flex-1 overflow-x-hidden p-4 md:p-8">{children}</main>
          </div>
        </div>
      </PeriodProvider>
    </AudienceProvider>
  );
}
