"""
tally_importer.py — Build Tally XML for Purchase vouchers and POST to Tally Prime.

Public functions:
  build_purchase_xml(invoice: dict) -> str
  post_to_tally(xml: str)          -> dict  {"success": bool, "message": str}
"""

import re
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import config

# ── XML Builder ───────────────────────────────────────────────────────────────

def build_purchase_xml(invoice: dict, with_inventory: bool = True) -> str:
    """
    Build a Tally Prime XML import envelope for a single Purchase voucher.

    Tally sign convention for Purchase voucher:
      Dr entries (Purchase A/c, Input CGST, Input SGST): ISDEEMEDPOSITIVE=Yes, AMOUNT negative
      Cr entry  (Supplier ledger):                        ISDEEMEDPOSITIVE=No,  AMOUNT positive

    Args:
        invoice:        validated dict from llm_parser.parse_invoice()
        with_inventory: if True (default), include ALLINVENTORYENTRIES.LIST (requires stock items
                        to exist in Tally).  If False, import as a pure accounting voucher
                        (no stock item dependency — amount/GST/supplier still recorded correctly).

    Returns:
        XML string ready to POST to Tally's HTTP server
    """
    supplier    = invoice["supplier_name"]
    inv_no      = invoice["invoice_number"]
    inv_date    = _parse_date(str(invoice.get("invoice_date") or "").strip())
    items       = invoice["items"]
    cgst        = float(invoice.get("cgst") or 0)
    sgst        = float(invoice.get("sgst") or 0)
    igst        = float(invoice.get("igst") or 0)
    total       = float(invoice["total_amount"])

    # Base amount (before GST) = total - cgst - sgst - igst
    base_amount = total - cgst - sgst - igst

    obj_view = "Invoice Voucher View" if with_inventory else "Accounting Voucher View"
    is_invoice = "Yes" if with_inventory else "No"

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<ENVELOPE>',
             '  <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>',
             '  <BODY>',
             '    <IMPORTDATA>',
             '      <REQUESTDESC>',
             '        <REPORTNAME>Vouchers</REPORTNAME>',
             '      </REQUESTDESC>',
             '      <REQUESTDATA>',
             '        <TALLYMESSAGE xmlns:UDF="TallyUDF">',
             f'          <VOUCHER VCHTYPE="Purchase" ACTION="Create" OBJVIEW="{obj_view}">',
             f'            <DATE>{inv_date}</DATE>',
             f'            <VOUCHERTYPENAME>Purchase</VOUCHERTYPENAME>',
             f'            <VOUCHERNUMBER>{_esc(inv_no)}</VOUCHERNUMBER>',
             f'            <PARTYLEDGERNAME>{_esc(supplier)}</PARTYLEDGERNAME>',
             f'            <ISINVOICE>{is_invoice}</ISINVOICE>',
             ]

    # ── Inventory entries (one per item) — skipped in accounting-only mode ────
    if with_inventory:
        for item in items:
            name   = item["name"]
            qty    = item["quantity"]
            unit   = item.get("unit") or "Pcs"
            rate   = item["rate"]
            amount = item["amount"]
            lines += [
                f'            <ALLINVENTORYENTRIES.LIST>',
                f'              <STOCKITEMNAME>{_esc(name)}</STOCKITEMNAME>',
                f'              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>',
                f'              <RATE>{rate:.2f}/{unit}</RATE>',
                f'              <AMOUNT>-{amount:.2f}</AMOUNT>',
                f'              <ACTUALQTY>{qty} {unit}</ACTUALQTY>',
                f'              <BILLEDQTY>{qty} {unit}</BILLEDQTY>',
                f'            </ALLINVENTORYENTRIES.LIST>',
            ]

    # ── Ledger entries ────────────────────────────────────────────────────────

    # Purchase A/c — Dr
    lines += [
        f'            <ALLLEDGERENTRIES.LIST>',
        f'              <LEDGERNAME>Purchase</LEDGERNAME>',
        f'              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>',
        f'              <AMOUNT>-{base_amount:.2f}</AMOUNT>',
        f'            </ALLLEDGERENTRIES.LIST>',
    ]

    # Input CGST — Dr (only if CGST present)
    if cgst > 0:
        lines += [
            f'            <ALLLEDGERENTRIES.LIST>',
            f'              <LEDGERNAME>Input CGST</LEDGERNAME>',
            f'              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>',
            f'              <AMOUNT>-{cgst:.2f}</AMOUNT>',
            f'            </ALLLEDGERENTRIES.LIST>',
        ]

    # Input SGST — Dr (only if SGST present)
    if sgst > 0:
        lines += [
            f'            <ALLLEDGERENTRIES.LIST>',
            f'              <LEDGERNAME>Input SGST</LEDGERNAME>',
            f'              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>',
            f'              <AMOUNT>-{sgst:.2f}</AMOUNT>',
            f'            </ALLLEDGERENTRIES.LIST>',
        ]

    # Input IGST — Dr (only if IGST present, inter-state purchase)
    if igst > 0:
        lines += [
            f'            <ALLLEDGERENTRIES.LIST>',
            f'              <LEDGERNAME>Input IGST</LEDGERNAME>',
            f'              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>',
            f'              <AMOUNT>-{igst:.2f}</AMOUNT>',
            f'            </ALLLEDGERENTRIES.LIST>',
        ]

    # Supplier (Sundry Creditor) — Cr
    lines += [
        f'            <ALLLEDGERENTRIES.LIST>',
        f'              <LEDGERNAME>{_esc(supplier)}</LEDGERNAME>',
        f'              <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>',
        f'              <AMOUNT>{total:.2f}</AMOUNT>',
        f'            </ALLLEDGERENTRIES.LIST>',
    ]

    lines += [
        '          </VOUCHER>',
        '        </TALLYMESSAGE>',
        '      </REQUESTDATA>',
        '    </IMPORTDATA>',
        '  </BODY>',
        '</ENVELOPE>',
    ]

    return "\n".join(lines)


# ── Stock Item auto-creation ──────────────────────────────────────────────────

def build_stockitems_xml(items: list) -> str:
    """
    Build a Tally XML envelope that creates each item as a Stock Item master.
    Safe to send even if items already exist — Tally returns a non-fatal error
    for duplicates which ensure_stock_items() silently ignores.
    """
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<ENVELOPE>',
             '  <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>',
             '  <BODY><IMPORTDATA>',
             '    <REQUESTDESC><REPORTNAME>All Masters</REPORTNAME></REQUESTDESC>',
             '    <REQUESTDATA>']
    for item in items:
        name = _esc(str(item.get("name", "")).strip())
        if not name:
            continue
        lines += [
            f'      <TALLYMESSAGE xmlns:UDF="TallyUDF">',
            f'        <STOCKITEM NAME="{name}" ACTION="Create">',
            f'          <NAME>{name}</NAME>',
            f'          <PARENT></PARENT>',
            f'          <BASEUNITS></BASEUNITS>',
            f'        </STOCKITEM>',
            f'      </TALLYMESSAGE>',
        ]
    lines += ['    </REQUESTDATA>', '  </IMPORTDATA></BODY>', '</ENVELOPE>']
    return "\n".join(lines)


def ensure_stock_items(items: list) -> str:
    """
    Create any missing stock items in Tally before importing a voucher.
    Returns the raw Tally response text for diagnostic purposes ('' on network error).
    Items that already exist cause a non-fatal duplicate response which is safe to ignore.
    """
    xml = build_stockitems_xml(items)
    try:
        resp = requests.post(
            config.TALLY_URL,
            data=xml.encode("utf-8"),
            headers={"Content-Type": "application/xml"},
            timeout=15,
        )
        return resp.text
    except Exception:
        return ""


# ── Ledger auto-creation ──────────────────────────────────────────────────────

def build_ledgers_xml(invoice: dict) -> str:
    """
    Build a Tally XML envelope that creates all ledgers required by the voucher:
      Purchase (under Purchase Accounts), Input CGST/SGST/IGST (under Duties & Taxes),
      and the supplier (under Sundry Creditors).
    Safe to send even if ledgers already exist — Tally returns a non-fatal duplicate.
    """
    supplier = _esc(str(invoice.get("supplier_name", "")).strip())
    cgst     = float(invoice.get("cgst") or 0)
    sgst     = float(invoice.get("sgst") or 0)
    igst     = float(invoice.get("igst") or 0)

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<ENVELOPE>',
             '  <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>',
             '  <BODY><IMPORTDATA>',
             '    <REQUESTDESC><REPORTNAME>All Masters</REPORTNAME></REQUESTDESC>',
             '    <REQUESTDATA>']

    # Purchase ledger (always needed for the voucher's Dr entry)
    lines += [
        '      <TALLYMESSAGE xmlns:UDF="TallyUDF">',
        '        <LEDGER NAME="Purchase" ACTION="Create">',
        '          <NAME>Purchase</NAME>',
        '          <PARENT>Purchase Accounts</PARENT>',
        '        </LEDGER>',
        '      </TALLYMESSAGE>',
    ]

    # GST input tax ledgers (only when the invoice has that tax)
    for gst_name, amount in [
        ("Input CGST", cgst),
        ("Input SGST", sgst),
        ("Input IGST", igst),
    ]:
        if amount > 0:
            lines += [
                f'      <TALLYMESSAGE xmlns:UDF="TallyUDF">',
                f'        <LEDGER NAME="{gst_name}" ACTION="Create">',
                f'          <NAME>{gst_name}</NAME>',
                f'          <PARENT>Duties &amp; Taxes</PARENT>',
                f'        </LEDGER>',
                f'      </TALLYMESSAGE>',
            ]

    # Supplier ledger (Sundry Creditor — the Cr entry)
    if supplier:
        lines += [
            f'      <TALLYMESSAGE xmlns:UDF="TallyUDF">',
            f'        <LEDGER NAME="{supplier}" ACTION="Create">',
            f'          <NAME>{supplier}</NAME>',
            f'          <PARENT>Sundry Creditors</PARENT>',
            f'        </LEDGER>',
            f'      </TALLYMESSAGE>',
        ]

    lines += ['    </REQUESTDATA>', '  </IMPORTDATA></BODY>', '</ENVELOPE>']
    return "\n".join(lines)


def ensure_ledgers(invoice: dict) -> str:
    """
    Create all required ledgers in Tally before importing a voucher.
    Returns the raw Tally response text for diagnostics ('' on network error).
    Ledgers that already exist cause a non-fatal duplicate response.
    """
    xml = build_ledgers_xml(invoice)
    try:
        resp = requests.post(
            config.TALLY_URL,
            data=xml.encode("utf-8"),
            headers={"Content-Type": "application/xml"},
            timeout=15,
        )
        return resp.text
    except Exception:
        return ""


# ── Tally HTTP POST ───────────────────────────────────────────────────────────

def post_to_tally(xml: str) -> dict:
    """
    POST a Tally XML import envelope to Tally Prime's HTTP server.

    Returns:
        {"success": True,  "message": "1 voucher(s) created"}
        {"success": False, "message": "error description"}
    """
    url = config.TALLY_URL  # e.g. http://localhost:9000

    try:
        resp = requests.post(
            url,
            data=xml.encode("utf-8"),
            headers={"Content-Type": "application/xml"},
            timeout=30,
        )
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "message": f"Cannot connect to Tally at {url}. Make sure Tally Prime is open."
        }
    except requests.exceptions.Timeout:
        return {"success": False, "message": "Tally did not respond within 30 seconds."}
    except Exception as e:
        return {"success": False, "message": str(e)}

    if resp.status_code != 200:
        return {"success": False, "message": f"Tally returned HTTP {resp.status_code}"}

    return _parse_tally_response(resp.text)


def _parse_tally_response(xml_text: str) -> dict:
    """Parse Tally's XML response to detect success or error."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        # Tally sometimes returns plain text on success
        if "Created" in xml_text or "created" in xml_text:
            return {"success": True, "message": "Voucher created successfully"}
        return {"success": False, "message": f"Unexpected response: {xml_text[:200]}"}

    # Check for LINEERROR elements
    errors = [el.text for el in root.iter("LINEERROR") if el.text]
    if errors:
        return {"success": False, "message": "; ".join(errors)}

    # Check CREATED count
    created = root.findtext(".//CREATED") or root.findtext("CREATED")
    if created and int(created) > 0:
        return {"success": True, "message": f"{created} voucher(s) created in Tally"}

    # Check for any error text
    error_el = root.find(".//ERROR") or root.find("ERROR")
    if error_el is not None and error_el.text:
        return {"success": False, "message": error_el.text.strip()}

    # Generic fallback — if no error found, assume success
    return {"success": True, "message": "Import request sent to Tally"}


def _parse_date(raw: str) -> str:
    """
    Parse a date string in any common format and return YYYYMMDD for Tally.
    Raises ValueError if the date cannot be parsed (caller shows error to user).

    Year validation (2000-2099) prevents Python's %Y from silently accepting
    2-digit years as year 25 AD (e.g. "25-02-25" → "00250225") which Tally
    rejects as "Voucher date is missing".
    """
    for fmt in (
        "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y%m%d",
        "%d-%b-%Y", "%d %b %Y", "%d %B %Y", "%Y/%m/%d",
        "%d-%m-%y", "%d/%m/%y",   # 2-digit year fallbacks (%y → 2000-2068)
    ):
        try:
            dt = datetime.strptime(raw, fmt)
            if dt.year < 2000 or dt.year > 2099:
                continue  # reject implausible years (e.g. year 25 AD from 2-digit input)
            return dt.strftime("%Y%m%d")
        except ValueError:
            continue
    raise ValueError(
        f"Cannot read the bill date '{raw}'. "
        f"Please enter it as YYYY-MM-DD (e.g. 2025-02-25)."
    )


def _esc(text: str) -> str:
    """Escape special XML characters in text."""
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;"))
