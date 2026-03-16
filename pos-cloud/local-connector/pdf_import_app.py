"""
pdf_import_app.py — Supplier Bill → Tally (local Streamlit UI).
Launched by launcher.pyw — runs on http://localhost:8501 on the Tally PC.
User-friendly: plain language, auto-reads PDF on upload, no technical jargon.
"""

import csv
import io
import json
import logging
import os
import sys
from datetime import datetime
import streamlit as st
import pandas as pd

from pdf_extractor import extract_text
from llm_parser import parse_invoice
import tally_importer
import config

# ─────────────────────────────────────────────────────────────────────────────
# Page setup
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Supplier Bill → Tally",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdf_import_log.csv")

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _write_log(filename, supplier, inv_no, amount, status, note=""):
    cols = ["Date", "Bill File", "Supplier", "Bill No.", "Amount (₹)", "Status", "Note"]
    exists = os.path.exists(LOG_PATH)
    with open(LOG_PATH, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        if not exists:
            w.writeheader()
        w.writerow({
            "Date":        datetime.now().strftime("%d %b %Y, %I:%M %p"),
            "Bill File":   filename,
            "Supplier":    supplier,
            "Bill No.":    inv_no,
            "Amount (₹)":  f"{float(amount):,.2f}",
            "Status":      "✅ Saved" if status == "success" else "❌ Failed",
            "Note":        note,
        })


def _load_log():
    if not os.path.exists(LOG_PATH):
        return None
    try:
        return pd.read_csv(LOG_PATH).iloc[::-1].head(50)
    except Exception:
        return None


def _totals_ok(items, cgst, sgst, igst, total) -> str:
    """Return warning string if amounts don't add up, else ''."""
    items_sum = sum(float(i.get("amount") or 0) for i in items)
    expected  = round(items_sum + cgst + sgst + igst, 2)
    if abs(expected - round(total, 2)) > 1.0:
        return (f"Items subtotal ₹{items_sum:,.2f} + GST ₹{cgst+sgst+igst:,.2f} "
                f"= ₹{expected:,.2f}, but Grand Total shows ₹{total:,.2f}. "
                f"Please check the amounts.")
    return ""


def _friendly_error(msg: str) -> str:
    msg = msg or ""
    lo = msg.lower()
    if "connect" in lo or "refused" in lo:
        return "Tally Prime is not open. Please open Tally first and try again."
    if "timeout" in lo:
        return "Tally is taking too long to respond. Make sure Tally is not busy."
    if "stock item" in lo or ("does not exist" in lo and "ledger" not in lo):
        return (f"A product in this bill could not be added to Tally automatically. "
                f"Please create the product in Tally first, then try saving again.\n\n_{msg}_")
    if "ledger" in lo or "not found" in lo:
        return (f"Tally could not find one of the accounts. "
                f"The supplier may need to be created in Tally first.\n\n_{msg}_")
    if "date" in lo and ("missing" in lo or "invalid" in lo):
        return (f"The bill date is outside Tally's active financial year. "
                f"**In Tally:** press **F2** (Change Period) and set the period to include "
                f"the bill date, then try saving again. "
                f"If the Bill Date field above is blank, fill it in as YYYY-MM-DD first.\n\n_{msg}_")
    return msg


def _tally_status():
    try:
        import urllib.request
        urllib.request.urlopen(config.TALLY_URL, timeout=2)
        return True
    except Exception:
        return False


def _get_last_sync() -> str:
    try:
        base = (os.path.dirname(sys.executable) if getattr(sys, "frozen", False)
                else os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base, "last_sync.json")
        with open(path) as f:
            d = json.load(f).get("last_sync_date", "")
        return datetime.strptime(d, "%Y-%m-%d").strftime("%d %b %Y") if d else ""
    except Exception:
        return ""


def _run_sync() -> dict:
    import tally_connector
    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s – %(message)s", datefmt="%H:%M:%S"))
    logging.getLogger().addHandler(handler)
    success = True
    try:
        tally_connector.run()
    except SystemExit as e:
        success = (e.code == 0)
    except Exception as e:
        success = False
        logging.getLogger("sync").error("Error: %s", e)
    finally:
        logging.getLogger().removeHandler(handler)
    return {"success": success, "log": buf.getvalue() or "(no output)"}


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar — Sync Now
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("🔄 Sync Sales to Cloud")
    last = _get_last_sync()
    if last:
        st.caption(f"Last sync: **{last}**")
    else:
        st.caption("Last sync: _never_")
    st.caption(f"Store: `{config.STORE_ID or 'not configured'}`")

    if st.button("▶ Sync Now", type="primary", use_container_width=True):
        with st.spinner("Syncing Tally data to cloud…"):
            res = _run_sync()
        if res["success"]:
            st.success("✅ Sync complete!")
            st.rerun()
        else:
            st.error("❌ Sync failed. See log below.")
        with st.expander("Sync log", expanded=not res["success"]):
            st.code(res["log"], language="text")

st.title("🧾 Supplier Bill → Tally")
st.caption("Upload your supplier's PDF bill — we'll read it and save it directly into Tally.")

# Status row
tally_ok = _tally_status()
ai_ok    = bool(config.GROQ_API_KEY)

c1, c2, c3 = st.columns([1, 1, 6])
c1.markdown(
    "🟢 **Tally Open**" if tally_ok else "🔴 **Tally Closed**",
    help="Tally Prime must be open on this computer."
)
c2.markdown(
    "🟢 **AI Ready**" if ai_ok else "🔴 **AI Key Missing**",
    help="Groq API key from config.ini."
)

if not ai_ok:
    st.error("AI key is not set up. Please run the Setup Wizard again and enter your Groq AI key.")
    st.stop()

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# Step 1 — Upload
# ─────────────────────────────────────────────────────────────────────────────

st.subheader("① Select Supplier Bill")
st.caption("Drop the PDF here, or click Browse. You can select multiple bills at once.")

uploaded_files = st.file_uploader(
    "Select PDF bill(s)",
    type=["pdf"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)

if not uploaded_files:
    st.info("💡 Upload a supplier bill PDF above to get started. The AI will read it automatically.")
    log_df = _load_log()
    if log_df is not None:
        st.divider()
        st.subheader("📋 Previously Saved Bills")
        st.dataframe(log_df, use_container_width=True, hide_index=True)
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# Process each file
# ─────────────────────────────────────────────────────────────────────────────

for uploaded in uploaded_files:
    st.divider()

    file_key   = f"{uploaded.name}_{uploaded.size}"
    parsed_key = f"parsed_{file_key}"
    result_key = f"result_{file_key}"

    already_done = result_key in st.session_state and st.session_state[result_key]["success"]
    icon = "✅" if already_done else "📄"
    st.subheader(f"{icon} {uploaded.name}")

    # ── Auto-read on upload ───────────────────────────────────────────────────

    if parsed_key not in st.session_state:
        with st.spinner("📖 Reading your bill… (5–10 seconds)"):
            try:
                raw_text = extract_text(uploaded.getvalue())
            except Exception as e:
                st.error(
                    f"Could not read this file.\n\n"
                    f"Make sure it is a **computer-generated PDF** (not a photo or scan).\n\n"
                    f"Details: {e}"
                )
                continue

            try:
                invoice = parse_invoice(raw_text)
                st.session_state[parsed_key] = invoice
            except ValueError as e:
                st.warning(
                    f"The bill was read but some details could not be understood automatically. "
                    f"Please fill in the missing fields below.\n\n_{e}_"
                )
                st.session_state[parsed_key] = {
                    "supplier_name": "", "invoice_number": "", "invoice_date": "",
                    "items": [], "cgst": 0.0, "sgst": 0.0, "igst": 0.0, "total_amount": 0.0
                }
            except RuntimeError as e:
                st.error(f"Could not connect to the AI service. Check your internet connection.\n\n_{e}_")
                continue

    invoice = st.session_state[parsed_key]

    # ── Step 2 — Check Details ────────────────────────────────────────────────

    st.subheader("② Check the Bill Details")
    st.caption("The AI has filled in the details below. Please check them and correct anything that looks wrong.")

    h1, h2, h3 = st.columns(3)
    invoice["supplier_name"]  = h1.text_input("Supplier Name",     invoice.get("supplier_name", ""),  key=f"sup_{file_key}",  placeholder="e.g. Agro Wholesale")
    invoice["invoice_number"] = h2.text_input("Bill Number",       invoice.get("invoice_number", ""), key=f"inv_{file_key}",  placeholder="e.g. INV-2025-001")
    invoice["invoice_date"]   = h3.text_input("Bill Date (YYYY-MM-DD)", invoice.get("invoice_date", ""),  key=f"date_{file_key}", placeholder="e.g. 2025-02-25")

    st.write("**Items** — click any cell to correct a value:")

    items_df = pd.DataFrame(invoice.get("items", []))
    for col in ["name", "quantity", "unit", "rate", "amount", "gst_rate"]:
        if col not in items_df.columns:
            items_df[col] = ("" if col in ("name", "unit") else 0)

    edited_df = st.data_editor(
        items_df,
        column_config={
            "name":     st.column_config.TextColumn("Product Name",       width="large"),
            "quantity": st.column_config.NumberColumn("Qty",              format="%.2f", width="small"),
            "unit":     st.column_config.TextColumn("Unit",               width="small",
                                                     help="Bag, Pkt, Btl, Pcs, Box, Kg…"),
            "rate":     st.column_config.NumberColumn("Rate ₹",           format="%.2f"),
            "amount":   st.column_config.NumberColumn("Amount ₹",         format="%.2f"),
            "gst_rate": st.column_config.NumberColumn("GST %",            format="%d", width="small"),
        },
        num_rows="dynamic",
        use_container_width=True,
        key=f"items_{file_key}",
    )
    invoice["items"] = edited_df.to_dict("records")

    st.write("**Tax & Grand Total**")
    t1, t2, t3, t4 = st.columns(4)
    invoice["cgst"]         = t1.number_input("CGST ₹",        value=float(invoice.get("cgst") or 0),         key=f"cgst_{file_key}",  format="%.2f")
    invoice["sgst"]         = t2.number_input("SGST ₹",        value=float(invoice.get("sgst") or 0),         key=f"sgst_{file_key}",  format="%.2f")
    invoice["igst"]         = t3.number_input("IGST ₹",        value=float(invoice.get("igst") or 0),         key=f"igst_{file_key}",  format="%.2f")
    invoice["total_amount"] = t4.number_input("Grand Total ₹", value=float(invoice.get("total_amount") or 0), key=f"total_{file_key}", format="%.2f")

    st.session_state[parsed_key] = invoice

    # Totals mismatch
    warn = _totals_ok(invoice["items"], invoice["cgst"], invoice["sgst"],
                      invoice["igst"], invoice["total_amount"])
    if warn:
        st.warning(f"⚠️ Amount mismatch — {warn}")

    # ── Step 3 — Save to Tally ────────────────────────────────────────────────

    st.subheader("③ Save to Tally")

    # Duplicate-bill warning (check log for same bill number with prior success)
    inv_no_now = invoice.get("invoice_number", "").strip()
    if inv_no_now and result_key not in st.session_state:
        log_df_check = _load_log()
        if log_df_check is not None and "Bill No." in log_df_check.columns:
            prior_ok = log_df_check[
                (log_df_check["Bill No."] == inv_no_now) &
                (log_df_check["Status"].str.contains("Saved", na=False))
            ]
            if not prior_ok.empty:
                st.warning(
                    f"⚠️ Bill **{inv_no_now}** was already saved to Tally on "
                    f"{prior_ok.iloc[0]['Date']}. Save again only if you need to correct it."
                )

    if result_key in st.session_state:
        result = st.session_state[result_key]
        if result["success"]:
            st.success("✅ Bill saved to Tally successfully!")
        else:
            st.error(f"❌ Could not save. {_friendly_error(result['message'])}")
            if st.button("Try Again", key=f"retry_{file_key}"):
                del st.session_state[result_key]
                st.rerun()
    else:
        if not tally_ok:
            st.warning("⚠️ Tally Prime is not open. Please open Tally first, then click Save.")

        if st.button(
            "💾  Save to Tally",
            type="primary",
            key=f"save_{file_key}",
            disabled=not invoice.get("supplier_name"),
        ):
            try:
                xml     = tally_importer.build_purchase_xml(invoice, with_inventory=True)
                xml_acc = tally_importer.build_purchase_xml(invoice, with_inventory=False)
            except Exception as e:
                st.error(f"Could not prepare the bill for Tally: {e}")
                continue

            with st.spinner("Saving to Tally…"):
                ledger_resp   = tally_importer.ensure_ledgers(invoice)
                creation_resp = tally_importer.ensure_stock_items(invoice.get("items", []))
                st.session_state[f"ledger_resp_{file_key}"]   = ledger_resp
                st.session_state[f"creation_resp_{file_key}"] = creation_resp
                result = tally_importer.post_to_tally(xml)
                # If stock items still missing, fall back to accounting voucher (no inventory)
                if not result["success"] and (
                    "stock item" in result["message"].lower() or
                    "does not exist" in result["message"].lower()
                ):
                    result = tally_importer.post_to_tally(xml_acc)
                    if result["success"]:
                        result["message"] += " (accounting only — stock quantities not tracked)"

            st.session_state[result_key] = result
            _write_log(
                filename=uploaded.name,
                supplier=invoice.get("supplier_name", ""),
                inv_no=invoice.get("invoice_number", ""),
                amount=invoice.get("total_amount", 0),
                status="success" if result["success"] else "failed",
                note=result["message"],
            )
            st.rerun()

        with st.expander("🔧 Advanced — view raw data (for troubleshooting only)"):
            try:
                st.code(tally_importer.build_purchase_xml(invoice), language="xml")
            except Exception as e:
                st.caption(f"Cannot show: {e}")
            lr = st.session_state.get(f"ledger_resp_{file_key}", "")
            if lr:
                st.caption("Ledger creation response from Tally:")
                st.code(lr, language="xml")
            cr = st.session_state.get(f"creation_resp_{file_key}", "")
            if cr:
                st.caption("Stock item creation response from Tally:")
                st.code(cr, language="xml")

# ─────────────────────────────────────────────────────────────────────────────
# Log
# ─────────────────────────────────────────────────────────────────────────────

st.divider()
st.subheader("📋 Previously Saved Bills")
log_df = _load_log()
if log_df is not None:
    st.dataframe(log_df, use_container_width=True, hide_index=True)
else:
    st.info("No bills saved yet. Upload your first supplier bill above.")
