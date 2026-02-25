"""
llm_parser.py — Use Groq LLM to extract structured invoice data from PDF text.

Public function:
  parse_invoice(pdf_text: str) -> dict

Returns a validated dict:
  {
    "supplier_name": str,
    "invoice_number": str,
    "invoice_date": str,          # YYYY-MM-DD
    "items": [
      {"name": str, "quantity": float, "unit": str,
       "rate": float, "amount": float, "gst_rate": int}
    ],
    "cgst": float,
    "sgst": float,
    "igst": float,
    "total_amount": float
  }
"""

import json
import re
from groq import Groq
import config
from pdf_extractor import sanitize_text

# ── Prompt ────────────────────────────────────────────────────────────────────

_SYSTEM = """You are an invoice data extraction assistant for Indian retail businesses.
Extract structured data from the supplier invoice text provided.

Return ONLY a valid JSON object — no markdown, no explanation, no code blocks.
Use these exact field names. If a field cannot be determined, use null or 0.

JSON schema:
{
  "supplier_name": "string",
  "invoice_number": "string",
  "invoice_date": "YYYY-MM-DD",
  "items": [
    {
      "name": "string",
      "quantity": number,
      "unit": "string (e.g. Bag, Pkt, Btl, Pcs, Box, Kg)",
      "rate": number,
      "amount": number,
      "gst_rate": number (percentage as integer: 0, 5, 12, 18, or 28)
    }
  ],
  "cgst": number,
  "sgst": number,
  "igst": number,
  "total_amount": number
}

Rules:
- invoice_date must be in YYYY-MM-DD format
- All monetary values must be numbers (not strings)
- gst_rate is the GST percentage (e.g. 5, 12, 18) — not the GST amount
- If CGST and SGST are both present, set igst to 0
- If only IGST is present, set cgst and sgst to 0
- total_amount is the final payable amount including GST
- Extract ALL line items shown in the invoice"""

_USER_TEMPLATE = """Extract invoice data from the following supplier bill text:

---
{text}
---

Return only the JSON object."""


# ── Parser ────────────────────────────────────────────────────────────────────

def parse_invoice(pdf_text: str) -> dict:
    """
    Send sanitized PDF text to Groq LLM and return structured invoice data.

    Args:
        pdf_text: Raw text extracted from PDF (will be sanitized internally)

    Returns:
        Validated invoice dict

    Raises:
        ValueError: if LLM response cannot be parsed as valid invoice JSON
        RuntimeError: if Groq API call fails
    """
    if not config.GROQ_API_KEY:
        raise RuntimeError(
            "Groq API key not configured. "
            "Add api_key under [groq] section in config.ini"
        )

    # Sanitize before sending to external API
    clean_text = sanitize_text(pdf_text)

    client = Groq(api_key=config.GROQ_API_KEY)

    try:
        response = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user",   "content": _USER_TEMPLATE.format(text=clean_text)},
            ],
            temperature=0.1,   # low temperature for deterministic extraction
            max_tokens=2048,
        )
    except Exception as e:
        raise RuntimeError(f"Groq API error: {e}") from e

    raw_response = response.choices[0].message.content.strip()

    # Strip markdown code fences if present (safety net)
    raw_response = re.sub(r'^```(?:json)?\s*', '', raw_response, flags=re.M)
    raw_response = re.sub(r'\s*```$', '', raw_response, flags=re.M)
    raw_response = raw_response.strip()

    try:
        data = json.loads(raw_response)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"LLM returned invalid JSON: {e}\n\nRaw response:\n{raw_response[:500]}"
        ) from e

    return _validate(data)


def _validate(data: dict) -> dict:
    """Ensure required fields exist and have correct types."""
    errors = []

    if not data.get("supplier_name"):
        errors.append("supplier_name is missing")
    if not data.get("invoice_number"):
        errors.append("invoice_number is missing")
    if not data.get("invoice_date"):
        errors.append("invoice_date is missing")

    items = data.get("items")
    if not items or not isinstance(items, list) or len(items) == 0:
        errors.append("items list is empty or missing")
    else:
        for i, item in enumerate(items):
            for field in ("name", "quantity", "rate", "amount"):
                if item.get(field) is None:
                    errors.append(f"items[{i}].{field} is missing")

    if errors:
        raise ValueError("Invoice extraction incomplete:\n" + "\n".join(f"  - {e}" for e in errors))

    # Coerce numeric fields to float (LLM sometimes returns strings)
    for field in ("cgst", "sgst", "igst", "total_amount"):
        try:
            data[field] = float(data.get(field) or 0)
        except (TypeError, ValueError):
            data[field] = 0.0

    for item in data["items"]:
        for field in ("quantity", "rate", "amount"):
            try:
                item[field] = float(item.get(field) or 0)
            except (TypeError, ValueError):
                item[field] = 0.0
        try:
            item["gst_rate"] = int(item.get("gst_rate") or 0)
        except (TypeError, ValueError):
            item["gst_rate"] = 0
        item.setdefault("unit", "Pcs")

    return data
