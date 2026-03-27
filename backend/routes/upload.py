"""
backend/routes/upload.py — PDF upload and parsing endpoints.

pdfplumber is the workhorse here. It handles most CAMS/KFintech PDFs well,
but encrypted/scanned PDFs will fail silently (we log and return partial results).
We deliberately never raise 422 on partial extraction — the caller gets whatever
we could parse plus a parse_errors list to show the user what went wrong.

FIXME: Encrypted PDFs (common with brokerage statements) need a password unlock
       step. pdfplumber supports passwords but we'd need users to supply them.
"""
from __future__ import annotations

import io
import logging
import re
from datetime import datetime
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/upload", tags=["File Upload & Parsing"])

# CAMS date formats ordered by frequency in practice
_DATE_FORMATS = ["%d-%b-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d %b %Y"]

_FORM16_PATTERNS = {
    "gross_income": [
        r"(?:gross\s+salary|total\s+salary)[^\d]*([\d,]+\.?\d*)",
        r"1\s*\.\s*(?:gross\s+salary)[^\d]*([\d,]+\.?\d*)",
    ],
    "hra_received": [r"(?:HRA\s+received|house\s+rent\s+allowance)[^\d]*([\d,]+\.?\d*)"],
    "sec80c": [
        r"(?:80C|section\s+80\s*C|life\s+insurance|ppf|elss)[^\d]*([\d,]+\.?\d*)",
        r"(?:aggregate\s+of\s+deductible\s+amount\s+under\s+80C)[^\d]*([\d,]+\.?\d*)",
    ],
    "sec80d": [r"(?:80D|section\s+80\s*D|medical\s+insurance)[^\d]*([\d,]+\.?\d*)"],
    "nps_deduction": [r"(?:80CCD|nps|national\s+pension)[^\d]*([\d,]+\.?\d*)"],
}


def _import_pdfplumber():
    try:
        import pdfplumber  # type: ignore
        return pdfplumber
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="pdfplumber not installed. Run: pip install pdfplumber==0.11.0",
        )


def _clean_amount(raw: str) -> float | None:
    try:
        cleaned = re.sub(r"[^\d.\-]", "", raw.replace(",", ""))
        return float(cleaned) if cleaned else None
    except (ValueError, AttributeError):
        return None


def _extract_form16_fields(text: str) -> dict[str, float | None]:
    extracted: dict[str, float | None] = {}
    text_lower = text.lower()
    for field, patterns in _FORM16_PATTERNS.items():
        found = None
        for pattern in patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                found = _clean_amount(matches[0])
                if found is not None:
                    break
        extracted[field] = found
    return extracted


def _parse_date(raw: str) -> str | None:
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(raw.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _detect_format(header_text: str) -> str:
    h = header_text.lower()
    return "kfintech" if ("kfintech" in h or "karvy" in h or "transaction date" in h) else "cams"


def _parse_cams_row(cols: list[str]) -> dict | None:
    if len(cols) < 4:
        return None
    date_str = _parse_date(cols[0])
    if not date_str:
        return None
    amount = _clean_amount(cols[2]) if len(cols) > 2 else None
    if amount is None:
        return None
    return {
        "fund_name": cols[1].strip(),
        "date": date_str,
        "amount": amount,
        "nav": _clean_amount(cols[3]) if len(cols) > 3 else None,
    }


def _parse_kfintech_row(cols: list[str]) -> dict | None:
    # KFintech column order differs slightly from CAMS
    return _parse_cams_row(cols)


@router.post("/form16", summary="Parse Form 16 PDF and extract tax fields")
async def upload_form16(file: UploadFile = File(...)) -> dict[str, Any]:
    """
    Accept Form 16 Part B PDF. Returns extracted tax figures + any parse errors.
    Missing fields are None — check missing_fields list before trusting the output.
    """
    pdfplumber = _import_pdfplumber()

    try:
        contents = await file.read()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read uploaded file: {exc}")

    all_text = ""
    parse_errors: list[dict] = []

    try:
        with pdfplumber.open(io.BytesIO(contents)) as pdf:
            for i, page in enumerate(pdf.pages):
                try:
                    all_text += (page.extract_text() or "") + "\n"
                except Exception as exc:
                    logger.warning("Form16: failed to extract text from page %d: %s", i + 1, exc)
                    parse_errors.append({"page": i + 1, "reason": str(exc)})
    except Exception as exc:
        logger.error("Form16: pdfplumber could not open PDF from %s: %s", file.filename, exc)
        raise HTTPException(status_code=422, detail=f"Cannot open PDF: {exc}")

    extracted = _extract_form16_fields(all_text)
    missing_fields = [k for k, v in extracted.items() if v is None]

    return {
        "extracted": {
            "gross_income": extracted.get("gross_income"),
            "deductions": {
                "hra_received": extracted.get("hra_received"),
                "sec80c": extracted.get("sec80c"),
                "sec80d": extracted.get("sec80d"),
                "nps_deduction": extracted.get("nps_deduction"),
            },
        },
        "missing_fields": missing_fields,
        "parse_errors": parse_errors,
    }


@router.post("/cams-statement", summary="Parse CAMS/KFintech Statement PDF")
async def upload_cams_statement(file: UploadFile = File(...)) -> dict[str, Any]:
    """
    Parse a CAMS or KFintech consolidated account statement PDF.
    Auto-detects format from page 1-3 headers. Returns transactions list + parse errors.
    """
    pdfplumber = _import_pdfplumber()

    try:
        contents = await file.read()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read uploaded file: {exc}")

    transactions: list[dict] = []
    parse_errors: list[dict] = []
    detected_format = "unknown"
    header_text = ""

    _HEADER_KEYWORDS = {"date", "fund name", "nav", "amount", "description", "transaction date"}

    try:
        with pdfplumber.open(io.BytesIO(contents)) as pdf:
            for i, page in enumerate(pdf.pages):
                try:
                    page_text = page.extract_text() or ""

                    if i < 3:
                        header_text += page_text
                    if i == 0:
                        detected_format = _detect_format(header_text)

                    parse_fn = _parse_kfintech_row if detected_format == "kfintech" else _parse_cams_row

                    for table in (page.extract_tables() or []):
                        for row in (table or []):
                            if not row:
                                continue
                            try:
                                cols = [str(c or "").strip() for c in row]
                                joined = " ".join(cols).lower()
                                if any(kw in joined for kw in _HEADER_KEYWORDS):
                                    continue
                                txn = parse_fn(cols)
                                if txn:
                                    transactions.append(txn)
                            except Exception as row_exc:
                                logger.debug("CAMS: skipped malformed row on page %d: %s", i + 1, row_exc)

                except Exception as exc:
                    logger.warning("CAMS: failed to process page %d of %s: %s", i + 1, file.filename, exc)
                    parse_errors.append({"page": i + 1, "reason": str(exc)})

    except Exception as exc:
        logger.error("CAMS: pdfplumber could not open PDF from %s: %s", file.filename, exc)
        raise HTTPException(status_code=422, detail=f"Cannot open PDF: {exc}")

    return {
        "detected_format": detected_format,
        "transaction_count": len(transactions),
        "transactions": transactions,
        "parse_errors": parse_errors,
    }
