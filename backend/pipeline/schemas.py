"""Pydantic schemas Claude must fill during extraction (tool-use structured output).

The extraction prompt forces Claude to return THESE shapes; anything else is
rejected. Values must be exactly as printed (costs negative), with the page
number the value was read from.
"""
from pydantic import BaseModel, Field


class ExtractedLineItem(BaseModel):
    line_code: str = Field(description="Canonical code, e.g. revenue, cost_of_sales, gross_profit, admin_expenses, operating_profit, cash, debtors, creditors_lt_1yr, cf_operating, closing_cash")
    label: str = Field(description="Label exactly as printed in the document")
    value: float = Field(description="Value exactly as printed. Costs/outflows negative. No thousands separators.")
    period_label: str = Field(description="FY24 | FY25 | HY25 | HY26")
    statement: str = Field(description="pnl | bs | cf | kpi")
    page_number: int = Field(description="1-based page of the PDF where this value appears")
    confidence: float = Field(ge=0, le=1, description="Extraction confidence; <0.9 flags human review")


class ExtractedStatement(BaseModel):
    document_filename: str
    line_items: list[ExtractedLineItem]
    notes: str = Field(default="", description="Anything ambiguous a human should review")
