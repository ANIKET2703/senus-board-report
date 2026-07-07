# Senus PLC Board Report: one-page write-up

**Aniket Nimbalkar · Assiduous Technology Graduate Assessment**

**Live demo:** https://senus-board-report-aniket.vercel.app · **Video:** https://youtu.be/JeynALgTRCs · **Repo:** https://github.com/ANIKET2703/senus-board-report · Login: `ceo@senus.com` / `senus2030`

## What I built

A platform that turns Senus PLC's published investor documents into an interactive board
report for Management, the Board, Equity Investors and Credit Providers. Claude vision
extracts the financials from the source PDFs, including the two key documents that are
scanned images with no text layer, into a PostgreSQL database where every figure keeps
its source document, page, extraction method and confidence. A unit-tested metrics
engine computes the board metrics (growth, margins, EBITDA to FCF bridge, cash runway,
working capital, DSCR, ROCE, and a market-based valuation view: EV/LTM revenue of
17.7x compressing to 2.4x by FY30 if the Senus 2030 commitment is delivered). Claude
writes audience-specific commentary and answers free-form questions with page-level
citations, using validated facts only.

## The design principle

AI extracts and explains; deterministic code computes. LLMs read scanned accounts well
and do arithmetic badly, so the boundary is strict: extraction output must pass 24
accounting-identity checks before it counts as a fact, metrics are pure functions
covered by 43 tests against hand-computed values, and commentary is checked after
generation. Any number that cannot be traced back to a validated fact causes the
commentary to be rejected.

## Three things worth a closer look

1. **The pipeline caught real errors in Senus's published filings**: a EUR 1,000 gross
   profit tie-out inconsistency in the HY26 results PR and a EUR 50 goodwill
   discrepancy between its notes and balance sheet. The platform shows these as
   data-quality findings instead of silently correcting them. It also records openly
   that Senus publishes no monthly data, which is why there are no MoM views: I was not
   willing to invent numbers to fill a chart.
2. **Honest finance on a pre-profit micro-cap.** DSCR is -50.3x at FY25. Textbook
   coverage ratios mislead when EBITDA is negative, so metrics carry plain caveats
   (debt service is equity-funded until the FY2028 EBITDA-positive guidance) and the
   report treats runway (10.5 months at Dec-25) as the number that actually matters.
3. **Audience-aware product thinking.** One validated dataset, four lenses. Credit
   providers land on solvency and runway; investors on growth and an interactive
   Senus 2030 model with adjustable assumptions, which is honest about the gap between
   HY26's 4.1% growth and the 50% CAGR commitment.

## Stack and engineering

FastAPI, SQLAlchemy and PostgreSQL (SQLite fallback for zero-setup runs); local
embeddings with a BM25 fallback for retrieval; Next.js 14, TypeScript, Tailwind and
Recharts; Docker Compose; GitHub Actions CI that re-runs the accounting-identity checks
on every push. The app seeds from versioned, human-validated extraction output, so it
deploys deterministically and runs without an API key. `make ingest` re-runs the live
Claude pipeline when new filings are published.

## How I worked

I read the filings first and recorded every figure with its page reference
(docs/FINANCIAL_FACTS.md), then designed the system around one rule: nothing reaches
the report unless deterministic checks pass it. AI tooling was part of my development
toolchain, as the brief invites; its output was reviewed line by line and every number
was verified by me against the source documents. The design decisions and their
reasoning are mine, written up in docs/ARCHITECTURE.md.
