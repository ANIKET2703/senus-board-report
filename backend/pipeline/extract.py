"""AI extraction: PDF -> structured financial line items.

Routing:
  * pages WITH a text layer   -> pdfplumber text -> Claude (text prompt)
  * pages WITHOUT text layer  -> pdf2image render @150dpi -> Claude vision

Both paths force structured output through the ExtractedStatement tool schema
(pipeline/schemas.py). Requires ANTHROPIC_API_KEY. Cost to re-run the full
corpus: ~USD 1-2.

Run: python -m pipeline.run --extract
"""
from __future__ import annotations

import base64
import io
import json
import os
from pathlib import Path

import pdfplumber
from anthropic import Anthropic

from pipeline.schemas import ExtractedStatement

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")

EXTRACTION_TOOL = {
    "name": "record_extracted_statement",
    "description": "Record financial line items extracted from the document, exactly as printed.",
    "input_schema": ExtractedStatement.model_json_schema(),
}

SYSTEM = """You are a forensic financial data extractor working on published
company filings. Extract every financial statement line item you can see.
Rules:
- Values EXACTLY as printed. Costs, losses and outflows are NEGATIVE numbers.
  Parentheses mean negative. Strip thousands separators.
- Never compute, infer, round or 'fix' a number. If a printed total looks
  inconsistent, record it as printed and mention it in `notes`.
- Record the exact 1-based PDF page each value appears on.
- period_label mapping: year ended 30 Jun 2024 -> FY24; year ended 30 Jun 2025
  -> FY25; 6 months to 31 Dec 2024 -> HY25; 6 months to 31 Dec 2025 -> HY26.
- Set confidence < 0.9 for any value that is blurry, ambiguous or partially
  obscured so a human reviews it."""


def page_has_text(page) -> bool:
    text = page.extract_text() or ""
    return len(text.strip()) > 40


def extract_document(pdf_path: Path, client: Anthropic) -> ExtractedStatement:
    content: list[dict] = []
    with pdfplumber.open(pdf_path) as pdf:
        text_pages = [i for i, p in enumerate(pdf.pages, 1) if page_has_text(p)]
        image_pages = [i for i in range(1, len(pdf.pages) + 1) if i not in text_pages]

        for i in text_pages:
            text = pdf.pages[i - 1].extract_text() or ""
            content.append({"type": "text", "text": f"--- PDF page {i} (text layer) ---\n{text}"})

    if image_pages:
        from pdf2image import convert_from_path
        images = convert_from_path(pdf_path, dpi=150,
                                   first_page=min(image_pages), last_page=max(image_pages))
        for offset, img in enumerate(images):
            page_no = min(image_pages) + offset
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            content.append({"type": "text", "text": f"--- PDF page {page_no} (scanned image) ---"})
            content.append({"type": "image", "source": {
                "type": "base64", "media_type": "image/png",
                "data": base64.b64encode(buf.getvalue()).decode()}})

    content.append({"type": "text",
                    "text": f"Document filename: {pdf_path.name}. Extract all financial line items."})

    response = client.messages.create(
        model=MODEL, max_tokens=16384, system=SYSTEM,
        tools=[EXTRACTION_TOOL],
        tool_choice={"type": "tool", "name": "record_extracted_statement"},
        messages=[{"role": "user", "content": content}],
    )
    if response.stop_reason == "max_tokens":
        raise RuntimeError(f"{pdf_path.name}: output truncated at max_tokens")
    tool_use = next(b for b in response.content if b.type == "tool_use")
    return ExtractedStatement.model_validate(tool_use.input)


# ------------------------------------------------------------------------
# Two-pass verification: any value the first pass extracted below the review
# threshold is independently re-read from ONLY its own page, rendered at
# higher DPI, without telling the model the first value (no anchoring).
# Agreement between two independent reads raises confidence; disagreement or
# illegibility pins the item in the human review queue (/api/validation/review-queue).
# ------------------------------------------------------------------------

CONFIDENCE_REVIEW_THRESHOLD = 0.9

VERIFY_SYSTEM = """You are re-reading a single financial figure from one page of
a published company filing. Report the value EXACTLY as printed: parentheses
mean negative, costs/outflows are negative, strip thousands separators. Never
infer or compute. If the figure is blurry or ambiguous, set legible=false."""

VERIFY_TOOL = {
    "name": "record_verified_value",
    "description": "Record the independently re-read value for one line item.",
    "input_schema": {
        "type": "object",
        "properties": {
            "value": {"type": "number", "description": "Value exactly as printed on this page"},
            "legible": {"type": "boolean", "description": "False if the value cannot be read with certainty"},
        },
        "required": ["value", "legible"],
    },
}


def _single_page_content(pdf_path: Path, page_no: int) -> list[dict]:
    """One page as text if it has a text layer, else as a 200dpi image."""
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_no - 1]
        if page_has_text(page):
            return [{"type": "text",
                     "text": f"--- PDF page {page_no} ---\n{page.extract_text()}"}]
    from pdf2image import convert_from_path
    img = convert_from_path(pdf_path, dpi=200, first_page=page_no, last_page=page_no)[0]
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return [{"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                         "data": base64.b64encode(buf.getvalue()).decode()}}]


def verify_low_confidence(result: ExtractedStatement, pdf_path: Path,
                          client: Anthropic) -> ExtractedStatement:
    for item in result.line_items:
        if item.confidence >= CONFIDENCE_REVIEW_THRESHOLD:
            continue
        content = _single_page_content(pdf_path, item.page_number)
        content.append({"type": "text", "text":
                        f"Re-read this line item from the page above: '{item.label}' "
                        f"({item.statement}, period {item.period_label})."})
        response = client.messages.create(
            model=MODEL, max_tokens=256, system=VERIFY_SYSTEM,
            tools=[VERIFY_TOOL],
            tool_choice={"type": "tool", "name": "record_verified_value"},
            messages=[{"role": "user", "content": content}])
        verdict = next(b for b in response.content if b.type == "tool_use").input
        if verdict.get("legible") and abs(float(verdict["value"]) - item.value) <= 0.5:
            item.confidence = 0.95  # two independent reads agree
            print(f"  verified {item.period_label} {item.line_code} = {item.value}")
        else:
            item.confidence = min(item.confidence, 0.5)  # stays in human review queue
            result.notes += (f" VERIFY-MISMATCH {item.period_label} {item.line_code}: "
                             f"pass1={item.value}, pass2={verdict.get('value')}, "
                             f"legible={verdict.get('legible')}.")
            print(f"  MISMATCH {item.period_label} {item.line_code}: "
                  f"{item.value} vs {verdict.get('value')} -> human review")
    return result


def extract_all(source_dir: Path, out_dir: Path) -> None:
    client = Anthropic()
    out_dir.mkdir(parents=True, exist_ok=True)
    failures = []
    for pdf_path in sorted(source_dir.glob("*.pdf")):
        out_file = out_dir / f"{pdf_path.stem}.extracted.json"
        if out_file.exists():
            print(f"skipping {pdf_path.name} (already extracted; delete the JSON to re-run)")
            continue
        print(f"extracting {pdf_path.name} ...")
        result = None
        for attempt in (1, 2):
            try:
                result = extract_document(pdf_path, client)
                break
            except Exception as exc:  # truncation, schema miss, transient API error
                print(f"  attempt {attempt} failed: {exc}")
        if result is None:
            failures.append(pdf_path.name)
            continue
        if any(i.confidence < CONFIDENCE_REVIEW_THRESHOLD for i in result.line_items):
            print("  low-confidence values found - running second-pass verification ...")
            result = verify_low_confidence(result, pdf_path, client)
        out_file.write_text(result.model_dump_json(indent=2))
        print(f"  -> {out_file.name}: {len(result.line_items)} line items")
    if failures:
        print(f"\nFAILED after retries: {failures}")
    else:
        print("\nall documents extracted")
