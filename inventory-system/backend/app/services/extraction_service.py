import json
import logging
import re
from typing import Optional

from app.config import settings
from app.models.invoice import (
    InvoiceData,
    InvoiceHeader,
    LineItem,
    TaxSummary,
    PaymentInfo,
)

logger = logging.getLogger(__name__)

try:
    import langextract as lx
    LX_AVAILABLE = True
except ImportError:
    LX_AVAILABLE = False
    logger.warning("langextract not installed. Using regex-based fallback extraction.")

EXTRACTION_PROMPT = """Extract all line items from this supplier invoice.
For each item, extract: item_name, quantity, unit, unit_price, total, gst_rate.
Also extract invoice header: supplier_name, invoice_number, invoice_date.
Also extract tax summary: cgst_amount, sgst_amount, igst_amount, total_tax.
Also extract payment info: payment_terms, due_date, bank_details.
Use exact text from the invoice. Do not infer or paraphrase."""


def _build_examples():
    """Build LangExtract examples (only when lx is available)."""
    return [
        lx.data.ExampleData(
            text=(
                "SUPPLIER: Metro Wholesale\nINV: MW-2024-5521\nDate: 10-Feb-2024\n"
                "Parle-G 50g 100 pcs @10.00 1000.00 GST 5%\n"
                "Britannia 100g 50 pcs @25.00 1250.00 GST 12%\n"
                "CGST: 250.00 SGST: 250.00\nPayment: Net 30, Due: 12-Mar-2024"
            ),
            extractions=[
                lx.data.Extraction(
                    extraction_class="invoice_header",
                    extraction_text="SUPPLIER: Metro Wholesale\nINV: MW-2024-5521\nDate: 10-Feb-2024",
                    attributes={
                        "supplier_name": "Metro Wholesale",
                        "invoice_number": "MW-2024-5521",
                        "invoice_date": "10-Feb-2024",
                    },
                ),
                lx.data.Extraction(
                    extraction_class="line_item",
                    extraction_text="Parle-G 50g 100 pcs @10.00 1000.00 GST 5%",
                    attributes={
                        "item_name": "Parle-G 50g",
                        "quantity": 100,
                        "unit": "pcs",
                        "unit_price": 10.00,
                        "total": 1000.00,
                        "gst_rate": "5%",
                    },
                ),
                lx.data.Extraction(
                    extraction_class="line_item",
                    extraction_text="Britannia 100g 50 pcs @25.00 1250.00 GST 12%",
                    attributes={
                        "item_name": "Britannia 100g",
                        "quantity": 50,
                        "unit": "pcs",
                        "unit_price": 25.00,
                        "total": 1250.00,
                        "gst_rate": "12%",
                    },
                ),
                lx.data.Extraction(
                    extraction_class="tax_summary",
                    extraction_text="CGST: 250.00 SGST: 250.00",
                    attributes={
                        "cgst_amount": 250.00,
                        "sgst_amount": 250.00,
                        "igst_amount": 0.0,
                        "total_tax": 500.00,
                    },
                ),
                lx.data.Extraction(
                    extraction_class="payment_info",
                    extraction_text="Payment: Net 30, Due: 12-Mar-2024",
                    attributes={
                        "payment_terms": "Net 30",
                        "due_date": "12-Mar-2024",
                        "bank_details": "",
                    },
                ),
            ],
        )
    ]


def extract_invoice_data(invoice_text: str) -> InvoiceData:
    """Extract structured invoice data from raw text."""
    if LX_AVAILABLE and settings.LANGEXTRACT_API_KEY:
        return _extract_with_langextract(invoice_text)
    return _extract_with_regex(invoice_text)


def _extract_with_langextract(invoice_text: str) -> InvoiceData:
    """Extract using LangExtract + Gemini."""
    result = lx.extract(
        text_or_documents=invoice_text,
        prompt_description=EXTRACTION_PROMPT,
        examples=_build_examples(),
        model_id="gemini-2.5-flash",
    )

    header = InvoiceHeader()
    line_items = []
    tax_summary = TaxSummary()
    payment_info = PaymentInfo()

    for extraction in result.extractions:
        attrs = extraction.attributes

        if extraction.extraction_class == "invoice_header":
            header = InvoiceHeader(
                supplier_name=str(attrs.get("supplier_name", "")),
                invoice_number=str(attrs.get("invoice_number", "")),
                invoice_date=str(attrs.get("invoice_date", "")),
            )
        elif extraction.extraction_class == "line_item":
            line_items.append(
                LineItem(
                    item_name=str(attrs.get("item_name", "")),
                    quantity=float(attrs.get("quantity", 0)),
                    unit=str(attrs.get("unit", "pcs")),
                    unit_price=float(attrs.get("unit_price", 0)),
                    total=float(attrs.get("total", 0)),
                    gst_rate=str(attrs.get("gst_rate", "")),
                )
            )
        elif extraction.extraction_class == "tax_summary":
            tax_summary = TaxSummary(
                cgst_amount=float(attrs.get("cgst_amount", 0)),
                sgst_amount=float(attrs.get("sgst_amount", 0)),
                igst_amount=float(attrs.get("igst_amount", 0)),
                total_tax=float(attrs.get("total_tax", 0)),
            )
        elif extraction.extraction_class == "payment_info":
            payment_info = PaymentInfo(
                payment_terms=str(attrs.get("payment_terms", "")),
                due_date=str(attrs.get("due_date", "")),
                bank_details=str(attrs.get("bank_details", "")),
            )

    return InvoiceData(
        header=header,
        line_items=line_items,
        tax_summary=tax_summary,
        payment_info=payment_info,
        raw_text=invoice_text,
    )


def _extract_with_regex(invoice_text: str) -> InvoiceData:
    """Fallback extraction using regex patterns (for local testing without LangExtract)."""
    logger.info("Using regex-based fallback extraction")

    # Extract header
    supplier = ""
    invoice_number = ""
    invoice_date = ""

    supplier_match = re.search(r"SUPPLIER:\s*(.+)", invoice_text, re.IGNORECASE)
    if supplier_match:
        supplier = supplier_match.group(1).strip()

    inv_match = re.search(r"INV(?:OICE)?(?:\s*(?:NO|#|:))?\s*:?\s*(\S+)", invoice_text, re.IGNORECASE)
    if inv_match:
        invoice_number = inv_match.group(1).strip()

    date_match = re.search(r"Date:\s*(.+)", invoice_text, re.IGNORECASE)
    if date_match:
        invoice_date = date_match.group(1).strip()

    header = InvoiceHeader(
        supplier_name=supplier,
        invoice_number=invoice_number,
        invoice_date=invoice_date,
    )

    # Extract line items: pattern like "Item Name  100 pcs @10.00 1000.00 GST 5%"
    line_items = []
    item_pattern = re.compile(
        r"^(.+?)\s+(\d+)\s+(pcs|kg|g|l|ml|box|pack|nos|unit)\s+@?([\d.]+)\s+([\d.]+)\s+(?:GST\s+)?(\d+%?)?",
        re.MULTILINE | re.IGNORECASE,
    )
    for m in item_pattern.finditer(invoice_text):
        line_items.append(
            LineItem(
                item_name=m.group(1).strip(),
                quantity=float(m.group(2)),
                unit=m.group(3).lower(),
                unit_price=float(m.group(4)),
                total=float(m.group(5)),
                gst_rate=m.group(6) or "",
            )
        )

    # Extract tax summary
    cgst = sgst = igst = total_tax = 0.0
    cgst_match = re.search(r"CGST:\s*([\d.]+)", invoice_text, re.IGNORECASE)
    sgst_match = re.search(r"SGST:\s*([\d.]+)", invoice_text, re.IGNORECASE)
    igst_match = re.search(r"IGST:\s*([\d.]+)", invoice_text, re.IGNORECASE)
    total_tax_match = re.search(r"Total\s*Tax:\s*([\d.]+)", invoice_text, re.IGNORECASE)

    if cgst_match:
        cgst = float(cgst_match.group(1))
    if sgst_match:
        sgst = float(sgst_match.group(1))
    if igst_match:
        igst = float(igst_match.group(1))
    if total_tax_match:
        total_tax = float(total_tax_match.group(1))
    else:
        total_tax = cgst + sgst + igst

    tax_summary = TaxSummary(
        cgst_amount=cgst,
        sgst_amount=sgst,
        igst_amount=igst,
        total_tax=total_tax,
    )

    # Extract payment info
    payment_terms = ""
    due_date = ""
    bank_details = ""

    payment_match = re.search(r"Payment:\s*(.+?)(?:,|$)", invoice_text, re.IGNORECASE)
    if payment_match:
        payment_terms = payment_match.group(1).strip()

    due_match = re.search(r"Due:\s*(.+?)(?:\n|$)", invoice_text, re.IGNORECASE)
    if due_match:
        due_date = due_match.group(1).strip()

    bank_match = re.search(r"Bank:\s*(.+?)(?:\n|$)", invoice_text, re.IGNORECASE)
    if bank_match:
        bank_details = bank_match.group(1).strip()

    payment_info = PaymentInfo(
        payment_terms=payment_terms,
        due_date=due_date,
        bank_details=bank_details,
    )

    return InvoiceData(
        header=header,
        line_items=line_items,
        tax_summary=tax_summary,
        payment_info=payment_info,
        raw_text=invoice_text,
    )
