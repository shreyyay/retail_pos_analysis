"""Parse Tally XML responses into clean Python dicts."""
import logging, xml.etree.ElementTree as ET
from datetime import date
from typing import Optional

logger = logging.getLogger(__name__)

_TALLY_GROUPS = {"Sales Accounts", "Purchase Accounts", "Cash-in-Hand",
                 "Bank Accounts", "Sundry Debtors", "Sundry Creditors"}


def _text(el, tag, default=""):
    node = el.find(tag)
    return (node.text or "").strip() if node is not None else default


def _float(el, tag, default=0.0):
    try:
        return float(_text(el, tag).replace(",", ""))
    except (ValueError, AttributeError):
        return default


def _tally_date(raw: str) -> Optional[str]:
    raw = raw.strip()
    if len(raw) == 8 and raw.isdigit():
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
    return None


def parse_sales_vouchers(xml_text: str) -> list[dict]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        logger.error("Sales XML parse error: %s", e); return []

    vouchers = []
    for v in root.iter("VOUCHER"):
        if _text(v, "VOUCHERTYPENAME").upper() != "SALES":
            continue
        vno = _text(v, "VOUCHERNUMBER")
        vdate = _tally_date(_text(v, "DATE"))
        if not vno or not vdate:
            continue

        cgst = sgst = igst = 0.0
        for le in v.findall(".//ALLLEDGERENTRIES.LIST"):
            name = _text(le, "LEDGERNAME").upper()
            amt = abs(_float(le, "AMOUNT"))
            if "CGST" in name: cgst += amt
            elif "SGST" in name: sgst += amt
            elif "IGST" in name: igst += amt

        items = []
        for inv in v.findall(".//ALLINVENTORYENTRIES.LIST"):
            iname = _text(inv, "STOCKITEMNAME")
            if not iname: continue
            qty_parts = _text(inv, "ACTUALQTY").split()
            items.append({
                "item_name": iname,
                "quantity": float(qty_parts[0]) if qty_parts else 0.0,
                "unit": qty_parts[1] if len(qty_parts) > 1 else "",
                "rate": _float(inv, "RATE"),
                "amount": abs(_float(inv, "AMOUNT")),
                "gst_rate": _text(inv, "GSTOVRDNSRATE"),
            })

        vouchers.append({
            "voucher_number": vno, "voucher_date": vdate,
            "total_amount": abs(_float(v, "AMOUNT")),
            "cgst_amount": cgst, "sgst_amount": sgst, "igst_amount": igst,
            "items": items,
        })
    return vouchers


def parse_purchase_vouchers(xml_text: str) -> list[dict]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        logger.error("Purchase XML parse error: %s", e); return []

    vouchers = []
    for v in root.iter("VOUCHER"):
        if _text(v, "VOUCHERTYPENAME").upper() != "PURCHASE":
            continue
        vno = _text(v, "VOUCHERNUMBER")
        vdate = _tally_date(_text(v, "DATE"))
        if not vno or not vdate: continue
        cgst = sgst = igst = 0.0
        for le in v.findall(".//ALLLEDGERENTRIES.LIST"):
            name = _text(le, "LEDGERNAME").upper()
            amt = abs(_float(le, "AMOUNT"))
            if "CGST" in name: cgst += amt
            elif "SGST" in name: sgst += amt
            elif "IGST" in name: igst += amt
        items = []
        for inv in v.findall(".//ALLINVENTORYENTRIES.LIST"):
            iname = _text(inv, "STOCKITEMNAME")
            if not iname: continue
            qty_parts = _text(inv, "ACTUALQTY").split()
            items.append({
                "item_name": iname,
                "quantity": float(qty_parts[0]) if qty_parts else 0.0,
                "unit": qty_parts[1] if len(qty_parts) > 1 else "",
                "rate": _float(inv, "RATE"), "amount": abs(_float(inv, "AMOUNT")),
            })
        vouchers.append({
            "voucher_number": vno, "voucher_date": vdate,
            "total_amount": abs(_float(v, "AMOUNT")),
            "cgst_amount": cgst, "sgst_amount": sgst, "igst_amount": igst, "items": items,
        })
    return vouchers


def parse_stock_summary(xml_text: str, snapshot_date: date) -> list[dict]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        logger.error("Stock XML parse error: %s", e); return []
    snap = snapshot_date.isoformat()
    items = []
    for si in root.iter("STOCKITEM"):
        name = _text(si, "NAME") or si.get("NAME", "")
        if not name: continue
        items.append({
            "item_name": name, "item_group": _text(si, "PARENT"),
            "unit": _text(si, "BASEUNITS"),
            "closing_qty": abs(_float(si, "CLOSINGBALANCE")),
            "closing_rate": abs(_float(si, "CLOSINGRATE")),
            "closing_value": abs(_float(si, "CLOSINGVALUE")),
            "snapshot_date": snap,
        })
    return items


def parse_ledger_balances(xml_text: str, snapshot_date: date) -> list[dict]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        logger.error("Ledger XML parse error: %s", e); return []
    snap = snapshot_date.isoformat()
    entries = []
    for group in root.iter("GROUP"):
        name = _text(group, "NAME") or group.get("NAME", "")
        if name not in _TALLY_GROUPS: continue
        entries.append({"ledger_group": name, "closing_balance": _float(group, "CLOSINGBALANCE"), "snapshot_date": snap})
    return entries


def parse_payment_receipts(payment_xml: str, receipt_xml: str) -> list[dict]:
    entries = []
    for xml_text, ptype in [(payment_xml, "Payment"), (receipt_xml, "Receipt")]:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            logger.error("%s XML parse error: %s", ptype, e); continue
        for v in root.iter("VOUCHER"):
            vno = _text(v, "VOUCHERNUMBER")
            vdate = _tally_date(_text(v, "DATE"))
            if not vno or not vdate: continue
            bank_or_cash = ""
            for le in v.findall(".//ALLLEDGERENTRIES.LIST"):
                ln = _text(le, "LEDGERNAME").lower()
                if ln in ("cash", "petty cash"):
                    bank_or_cash = "Cash"; break
                if "bank" in ln:
                    bank_or_cash = "Bank"; break
            entries.append({
                "voucher_number": vno, "voucher_date": vdate,
                "payment_type": ptype, "bank_or_cash": bank_or_cash,
                "amount": abs(_float(v, "AMOUNT")),
            })
    return entries
