import type { Metadata } from "next";
import { Bitter, Figtree } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/lib/theme";

// Senus brand typography (senus.com / corporate deck): Figtree body, Bitter headings
const figtree = Figtree({ subsets: ["latin"] });
const bitter = Bitter({ subsets: ["latin"], variable: "--font-bitter" });

export const metadata: Metadata = {
  title: "Senus PLC - Board Report",
  description: "AI-native board reporting platform for Senus PLC",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${figtree.className} ${bitter.variable}`}><ThemeProvider>{children}</ThemeProvider></body>
    </html>
  );
}
