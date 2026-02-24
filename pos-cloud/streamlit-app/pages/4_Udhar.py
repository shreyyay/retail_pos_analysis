"""Udhar (Credit) page — view, add, and update customer credit entries."""
from datetime import date

import pandas as pd
import streamlit as st

import db
import sidebar

st.set_page_config(page_title="Udhar", page_icon="💳", layout="wide")
store_id = sidebar.setup()
if not store_id:
    st.info("👈 Enter your Store ID in the sidebar to view data.")
    st.stop()

st.title("Udhar (Credit)")

# Filters
col1, col2 = st.columns(2)
with col1:
    status_filter = st.selectbox("Status", ["All", "Pending", "Paid"])
with col2:
    search = st.text_input("Search customer name")

# Build and run query
sql = (
    "SELECT id, customer_name, phone, items, amount, date_given, due_date, status "
    "FROM udhar WHERE store_id = %s"
)
params: list = [store_id]
if status_filter != "All":
    sql += " AND status = %s"
    params.append(status_filter)
if search:
    sql += " AND LOWER(customer_name) LIKE %s"
    params.append(f"%{search.lower()}%")
sql += " ORDER BY due_date ASC"

try:
    rows = db.run_query(sql, params)
except Exception as e:
    st.error(f"Database error: {e}")
    st.stop()

if rows:
    df = pd.DataFrame(rows)
    df["amount"] = df["amount"].apply(lambda x: f"₹{float(x):,.0f}")
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(f"{len(rows)} entries found")

    # Inline status update
    st.subheader("Update Entry")
    with st.form("update_udhar"):
        c1, c2 = st.columns(2)
        entry_id = c1.number_input("Entry ID", min_value=1, step=1)
        new_status = c2.selectbox("New Status", ["Pending", "Paid"])
        if st.form_submit_button("Update Status"):
            try:
                conn = db.get_connection()
                cur = conn.cursor()
                cur.execute(
                    "UPDATE udhar SET status=%s, updated_at=NOW() WHERE id=%s AND store_id=%s",
                    (new_status, int(entry_id), store_id),
                )
                conn.commit()
                cur.close()
                conn.close()
                st.success(f"Entry {int(entry_id)} marked as {new_status}.")
                st.rerun()
            except Exception as e:
                st.error(f"Update failed: {e}")
else:
    st.info("No entries found for the selected filters.")

st.divider()

# Add new entry
st.subheader("Add New Udhar Entry")
with st.form("add_udhar", clear_on_submit=True):
    c1, c2 = st.columns(2)
    customer_name = c1.text_input("Customer Name *")
    phone = c2.text_input("Phone")
    items = st.text_area("Items / Description")
    c3, c4 = st.columns(2)
    amount = c3.number_input("Amount (₹) *", min_value=0.0, step=1.0)
    date_given = c4.date_input("Date Given", value=date.today())
    due_date = st.date_input("Due Date", value=date.today())

    if st.form_submit_button("Add Entry", type="primary"):
        if not customer_name.strip():
            st.error("Customer name is required.")
        elif amount <= 0:
            st.error("Amount must be greater than 0.")
        else:
            try:
                conn = db.get_connection()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO udhar (store_id, customer_name, phone, items, amount, date_given, due_date, status) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, 'Pending')",
                    (store_id, customer_name.strip(), phone.strip(), items.strip(),
                     amount, date_given, due_date),
                )
                conn.commit()
                cur.close()
                conn.close()
                st.success(f"Added udhar entry for {customer_name}.")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to add entry: {e}")
