# Senus PLC: verified financial facts (human-checked baseline)

Before building the pipeline I read every source document and recorded each figure here
with its page reference. This file is the baseline the AI extraction output was checked
against, and the source of the expected values in the unit tests
(`tests/test_metrics_engine.py`).

All amounts in EUR unless stated.

---

## Entity timeline

| Entity | Note |
|---|---|
| ADF Farm Solutions Limited | Pre-IPO group (trading as Senus). Audited consolidated FY accounts to 30 June. |
| Senus Limited | Company balance sheet as at 8 Dec 2025 (scanned, pre-listing reorganisation). |
| Senus PLC | Listed entity. Euronext Access+ Dublin, admitted 22 Dec 2025. Ticker SENUS, ISIN IE000O0F49R3. Shares in issue: 2,561,332 (nominal EUR 0.01). |

Financial year ends 30 June. "FY25" = year ended 30 Jun 2025. "HY26" = 6 months ended 31 Dec 2025.

---

## Consolidated P&L (source: ADF FS FY25 p.10; HY26 PR consolidated P&L)

| Line | FY24 | FY25 | HY25 (6m to Dec-24) | HY26 (6m to Dec-25) |
|---|---|---|---|---|
| Turnover | 688,317 | 836,991 | 340,931 | 354,813 |
| Cost of sales | (255,840) | (188,541) | (69,600) | (64,861) |
| Gross profit | 432,477 | 648,450 | 272,331* | 289,952 |
| Distribution costs | (2,353) | (1,084) | 0 | 0 |
| Administrative expenses | (1,560,853) | (1,286,058) | (677,908) | (781,975) |
| Other operating income | 0 | 4,998 | 0 | 8,269 |
| Group operating loss | (1,130,729) | (633,694) | (405,577) | (483,753) |
| Other gains and losses | 319 | 0 | 0 | 0 |
| Interest payable | (48) | (2,074) | (1,036) | (1,391) |
| Loss before taxation | (1,130,458) | (635,768) | (406,613) | (485,144) |
| Tax credit/(charge) | 32,363 | 45,512 | 0 | 0 |
| Loss for period | (1,098,095) | (590,256) | (406,613) | (485,144) |

*The HY26 PR prints HY25 gross profit as 272,331, but turnover minus cost of sales is
340,931 - 69,600 = 271,331. That EUR 1,000 inconsistency is in the published source.
Values are recorded exactly as printed and the difference is flagged as a data-quality
finding in the app.

Margins (computed): gross margin FY24 62.8%, FY25 77.5%, HY25 79.8%, HY26 81.7%.

## Consolidated balance sheet (ADF FS p.11; HY26 PR)

| Line | 30 Jun 24 | 30 Jun 25 | 31 Dec 24 | 31 Dec 25 |
|---|---|---|---|---|
| Goodwill | - | - | 0 | 669,550 |
| Development costs (intangible) | - | - | 0 | 239,765 |
| Tangible assets | 65,390 | 48,788 | 65,363 | 42,006 |
| Debtors | 174,730 | 123,003 | 211,150 | 188,149 |
| Cash | 424,639 | 140,135 | 72,382 | 735,189 |
| Creditors < 1 yr | (90,078) | (243,846) | (90,111) | (387,105) |
| Contingent consideration | - | - | - | (850,000) |
| Creditors > 1 yr | 0 | (83,655) | (85,468) | (76,474) |
| Net assets/(liabilities) | 574,681 | (15,575) | 173,316* | 561,081 |
| Share capital | 144 | 144 | 144 | 25,000 |
| Share premium | 849,962 | 849,962 | 849,963 | 300,000 |
| Retained earnings | (275,425) | (865,681) | (676,790) | 236,081 |

*The HY26 PR labels the comparatives "as at 31-Dec-24". The post-listing capital
structure (share capital 25,000, premium 300,000, positive retained earnings 236,081)
reflects the reorganisation into Senus PLC. Flagged in the app rather than
force-reconciled.

## Consolidated cash flow (ADF FS p.15; HY26 PR)

| Line | FY24 | FY25 | HY25 | HY26 |
|---|---|---|---|---|
| Net cash used in operating | (1,166,697) | (374,820) | (450,181) | (410,291) |
| Net cash used in investing | (33,472) | (3,451) | 0 | (8,500) |
| Net cash from financing | (3,846) | 93,767 | 97,924 | 1,013,846 |
| Net movement | (1,204,015) | (284,504) | (352,257) | 595,055 |
| Opening cash | 1,628,654 | 424,639 | 424,639 | 140,135 |
| Closing cash | 424,639 | 140,135 | 72,382 | 735,189 |

FY25 detail: depreciation 20,381; interest paid 2,074; tax repaid 28,428;
working-capital movement +212,467 (debtors +68,811, creditors +143,656); new long-term
loan 100,000; repayment of short-term loan (6,233).
HY26 detail: depreciation 10,014; working capital +64,839; loan repayments (124,837);
share issue 1,138,683.

## Debt (ADF FS notes 12-13; HY26 PR)

- FY25 bank loans total 93,767: under 1yr 10,112; 1-2yr 10,500; 2-5yr 34,500; over 5yr 38,655. New EUR 100,000 SBCI-backed term loan drawn FY25.
- Directors' current accounts at FY25: 133,013 (Anthony Childs 50,000; Gerard Keenan 83,013).
- HY26: bank debt stated 76.5k (creditors > 1yr 76,474).

## Employees and directors (ADF FS notes 6, 16)

- Average employees: FY24 19, FY25 18.
- Directors' remuneration FY25: 213,485 + pension 10,437 (FY24: 312,988 + 21,370).

## KPIs and commercial (Information Document section 7.3, p.11, p.26; HY26 PR)

- FY25 customers: 138 accounts = 36 Enterprise + 98 Independent + 4 R&D.
- FY25 channel revenue mix: Enterprise 69%, Independent 4%, R&D 27%.
- FY25 geography: Ireland ~78%, ex-Ireland ~22% (11 jurisdictions active).
- FY25 avg Enterprise ACV: Soil 12,309; Terrain 21,524; ERA 58,900.
- R&D expenditure: ~17% of revenue FY25, ~22% FY24.
- HY26: ~700k deals closed across 21 enterprise customers; ~500k open pipeline; 10 deals of roughly 425k closed Nov-Dec 2025.

## Senus 2030 strategy targets

- Revenue CAGR of at least 50% (FY26-FY30, base FY25 = 836,991).
- EBITDA positive during FY2028.
- More than 100 Enterprise customers by FY2030; Enterprise ACV above 50,000.
- Ireland below 50% of revenue by end FY2030.

## Corporate events

- Loamin Ltd (UK geospatial AI) acquired HY26: goodwill 669,550, no cash consideration, contingent consideration 850,000 (performance-linked). Founders joined as Head of Research / Head of Software Engineering.
- EUR 1.1m equity raise completed (1,138,683 per cash flow).
- Direct listing, Euronext Access+ Dublin, 22 Dec 2025 (sponsor: Assiduous).
- Leadership transition PR, 24 Jun 2026.
- FY2028 EBITDA-positive guidance; FY26 outlook "in line with expectations", H1 seasonally weaker.

## Known data-quality findings (surfaced in the app)

1. HY25 gross profit line (272,331) vs turnover minus COS (271,331): EUR 1,000 inconsistency in the source PR.
2. HY26 PR goodwill: 669,550 on the balance sheet vs 669,500 in the notes (EUR 50 discrepancy).
3. HY26 PR balance-sheet comparatives labelled 31-Dec-24 show the pre-listing capital structure; post-listing equity was restated in the reorganisation.
4. ADF accounts and the Senus Limited balance sheet are scanned images with no text layer, so extraction had to be vision-based.
5. No monthly data is published in any filing, so MoM views cannot be built from source. Omitted rather than estimated.
