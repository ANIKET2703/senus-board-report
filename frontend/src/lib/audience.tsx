"use client";
import { createContext, useContext, useEffect, useState } from "react";

export type Audience = "board" | "management" | "investor" | "credit";
export const AUDIENCES: { id: Audience; label: string }[] = [
  { id: "board", label: "Board" },
  { id: "management", label: "Management" },
  { id: "investor", label: "Equity Investor" },
  { id: "credit", label: "Credit Provider" },
];

const Ctx = createContext<{ audience: Audience; setAudience: (a: Audience) => void }>({
  audience: "board", setAudience: () => {},
});

export function AudienceProvider({ children }: { children: React.ReactNode }) {
  const [audience, setAudience] = useState<Audience>("board");
  useEffect(() => {
    const saved = localStorage.getItem("audience") as Audience | null;
    if (saved) setAudience(saved);
  }, []);
  const set = (a: Audience) => { setAudience(a); localStorage.setItem("audience", a); };
  return <Ctx.Provider value={{ audience, setAudience: set }}>{children}</Ctx.Provider>;
}
export const useAudience = () => useContext(Ctx);
