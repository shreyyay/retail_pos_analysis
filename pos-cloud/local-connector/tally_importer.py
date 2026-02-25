"""
tally_importer.py — Build Tally XML for Purchase vouchers and POST to Tally Prime.

Public functions:
  build_purchase_xml(invoice: dict) -> str
  post_to_tally(xml: str)          -> dict  {"success": bool, "message": str}
"""

import re
import requests
import xml.etree.ElementTree as ET
import config

# ── XML Builder ───────────────────────────────────────────────────────────────

def build_purchase_xml(invoice: dict) -> str:
    """
    Build a Tally Prime XML import envelope for a single Purchase voucher.

    Tally sign convention for Purchase voucher:
      Dr entries (Purchase A/c, Input CGST, Input SGST): ISDEEMEDPOSITIVE=Yes, AMOUNT negative
      Cr entry  (Supplier ledger):                        ISDEEMEDPOSITIVE=No,  AMOUNT positive

    Args:
        invoice: validated dict from llm_parser.parse_invoice()

    Returns:
        XML string ready to POST to Tally's HTTP server
    """
    supplier    = invoice["supplier_name"]
    inv_no      = invoice["invoice_number"]
    inv_date    = invoice["invoice_date"].replace("-", "")  # YYYYMMDD
    items       = invoice["items"]
    cgst        = float(invoice.get("cgst") or 0)
    sgst        = float(invoice.get("sgst") or 0)
    igst        = float(invoice.get("igst") or 0)
    total       = float(invoice["total_amount"])

    # Base amount (before GST) = total - cgst - sgst - igst
    base_amount = total - cgst - sgst - igst

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
             f'          <VOUCHER VCHTYPE="Purchase" ACTION="Create" OBJVIEW="Invoice Voucher View">',
             f'            <DATE>{inv_date}</DATE>',
             f'            <VOUCHERTYPENAME>Purchase</VOUCHERTYPENAME>',
             f'            <VOUCHERNUMBER>{_esc(inv_no)}</VOUCHERNUMBER>',
             f'            <PARTYLEDGERNAME>{_esc(supplier)}</PARTYLEDGERNAME>',
             f'            <ISINVOICE>Yes</ISINVOICE>',
             ]

    # ── Inventory entries (one per item) ──────────────────────────────────────
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


def _esc(text: str) -> str:
    """Escape special XML characters in text."""
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;"))
