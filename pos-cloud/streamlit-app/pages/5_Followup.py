"""Follow-up page — manage customer follow-up tasks."""
from datetime import date
from typing import Optional

import pandas as pd
import streamlit as st

import db
import sidebar

st.set_page_config(page_title="Follow-up", page_icon="📞", layout="wide")
store_id = sidebar.setup()
if not store_id:
    st.info("👈 Enter your Store ID in the sidebar to view data.")
    st.stop()

st.title("Follow-up")

# Filters
col1, col2 = st.columns(2)
with col1:
    status_filter = st.selectbox("Status", ["All", "Open", "Closed"])
with col2:
    search = st.text_input("Search customer / salesperson")

# Build and run query
sql = (
    "SELECT id, customer_name, phone, salesperson, notes, "
    "followup_date, next_followup_date, status "
    "FROM followup WHERE store_id = %s"
)
params: list = [store_id]
if status_filter != "All":
    sql += " AND status = %s"
    params.append(status_filter)
if search:
    sql += " AND (LOWER(customer_name) LIKE %s OR LOWER(salesperson) LIKE %s)"
    params.extend([f"%{search.lower()}%", f"%{search.lower()}%"])
sql += " ORDER BY followup_date ASC"

try:
    rows = db.run_query(sql, params)
except Exception as e:
    st.error(f"Database error: {e}")
    st.stop()

if rows:
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(f"{len(rows)} entries found")

    # Inline update
    st.subheader("Update Entry")
    with st.form("update_followup"):
        c1, c2 = st.columns(2)
        entry_id = c1.number_input("Entry ID", min_value=1, step=1)
        new_status = c2.selectbox("New Status", ["Open", "Closed"])
        next_date = st.date_input("Next Follow-up Date", value=date.today())
        notes_update = st.text_area("Update Notes (appended to existing)")
        if st.form_submit_button("Update Entry"):
            try:
                # Fetch existing notes to append
                existing = db.run_query(
                    "SELECT notes FROM followup WHERE id=%s AND store_id=%s",
                    (int(entry_id), store_id),
                )
                current_notes = existing[0]["notes"] if existing else ""
                merged_notes = (
                    f"{current_notes}\n[{date.today()}] {notes_update}".strip()
                    if notes_update.strip()
                    else current_notes
                )
                conn = db.get_connection()
                cur = conn.cursor()
                cur.execute(
                    "UPDATE followup SET status=%s, next_followup_date=%s, notes=%s, "
                    "updated_at=NOW() WHERE id=%s AND store_id=%s",
                    (new_status, next_date, merged_notes, int(entry_id), store_id),
                )
                conn.commit()
                cur.close()
                conn.close()
                st.success(f"Entry {int(entry_id)} updated.")
                st.rerun()
            except Exception as e:
                st.error(f"Update failed: {e}")
else:
    st.info("No entries found for the selected filters.")

st.divider()

# Add new entry
st.subheader("Add New Follow-up Entry")
with st.form("add_followup", clear_on_submit=True):
    c1, c2 = st.columns(2)
    customer_name = c1.text_input("Customer Name *")
    phone = c2.text_input("Phone")
    salesperson = st.text_input("Salesperson *")
    notes = st.text_area("Notes")
    c3, c4 = st.columns(2)
    followup_date = c3.date_input("Follow-up Date", value=date.today())
    next_followup_date = c4.date_input("Next Follow-up Date (optional)", value=None)

    if st.form_submit_button("Add Entry", type="primary"):
        if not customer_name.strip():
            st.error("Customer name is required.")
        elif not salesperson.strip():
            st.error("Salesperson is required.")
        else:
            try:
                conn = db.get_connection()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO followup (store_id, customer_name, phone, salesperson, notes, "
                    "followup_date, next_followup_date, status) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, 'Open')",
                    (
                        store_id, customer_name.strip(), phone.strip(),
                        salesperson.strip(), notes.strip(),
                        followup_date,
                        next_followup_date if next_followup_date else None,
                    ),
                )
                conn.commit()
                cur.close()
                conn.close()
                st.success(f"Follow-up added for {customer_name}.")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to add entry: {e}")
