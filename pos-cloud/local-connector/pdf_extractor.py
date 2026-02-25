"""
pdf_extractor.py — Extract text from digital PDF files and sanitize before LLM.

Two public functions:
  extract_text(path_or_bytes)  -> str   raw text from all pages
  sanitize_text(raw: str)      -> str   redacts confidential fields, trims noise
"""

import re
import pdfplumber

# ── Constants ─────────────────────────────────────────────────────────────────

MAX_CHARS = 24_000   # ~6 000 tokens — stays within Groq context window

# ── PDF Text Extraction ───────────────────────────────────────────────────────

def extract_text(source) -> str:
    """
    Extract full text from a PDF.

    Args:
        source: file path (str/Path) OR bytes (from st.file_uploader)

    Returns:
        Raw concatenated text from all pages.
    """
    import io

    if isinstance(source, (bytes, bytearray)):
        source = io.BytesIO(source)

    pages = []
    with pdfplumber.open(source) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            text = page.extract_text(x_tolerance=2, y_tolerance=2) or ""
            if text.strip():
                pages.append(f"[Page {i}]\n{text}")

    return "\n\n".join(pages)


# ── Sanitization — Confidentiality Redaction ─────────────────────────────────

# Regex patterns for sensitive identifiers found in Indian supplier invoices
_PATTERNS = [
    # Bank account numbers (9–18 digits, often labelled "A/c", "Account")
    (re.compile(r'\b(?:A/?c\.?\s*:?\s*|Account\s*No\.?\s*:?\s*)?(\d{9,18})\b', re.I),
     '[BANK_REDACTED]'),

    # IFSC codes (e.g. HDFC0001234)
    (re.compile(r'\b[A-Z]{4}0[A-Z0-9]{6}\b'),
     '[IFSC_REDACTED]'),

    # GSTIN — 15-char format: 2-digit state + PAN + 1Z + 1 check digit
    (re.compile(r'\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}Z[A-Z\d]{1}\b'),
     '[GSTIN_REDACTED]'),

    # PAN — 5 letters, 4 digits, 1 letter (e.g. ABCDE1234F)
    (re.compile(r'\b[A-Z]{5}\d{4}[A-Z]\b'),
     '[PAN_REDACTED]'),

    # Indian mobile numbers — 10 digits starting with 6-9, with optional +91/0
    (re.compile(r'(?:\+91[-.\s]?|0)?[6-9]\d{9}\b'),
     '[PHONE_REDACTED]'),

    # Email addresses
    (re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'),
     '[EMAIL_REDACTED]'),
]


def sanitize_text(raw: str) -> str:
    """
    Redact confidential identifiers from extracted PDF text before sending to
    an external LLM API (Groq). Preserves all data needed for invoice parsing:
    supplier name, invoice number, date, item names, quantities, rates, amounts.

    Redacts:
      - Bank account numbers  → [BANK_REDACTED]
      - IFSC codes            → [IFSC_REDACTED]
      - GSTIN numbers         → [GSTIN_REDACTED]
      - PAN numbers           → [PAN_REDACTED]
      - Indian phone numbers  → [PHONE_REDACTED]
      - Email addresses       → [EMAIL_REDACTED]
    """
    text = raw

    # Apply each redaction pattern
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)

    # Remove non-printable / control characters (keep \n \t)
    text = re.sub(r'[^\x09\x0A\x0D\x20-\x7E\u00A0-\uFFFF]', '', text)

    # Collapse 3+ consecutive blank lines to 2
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Truncate to MAX_CHARS with a notice
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS]
        text += "\n\n[... PDF truncated for LLM context limit ...]"

    return text.strip()
