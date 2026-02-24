"""Overview page — KPIs, overdue udhar, low stock."""
import pandas as pd
import streamlit as st

import sidebar
from analytics import get_low_stock, get_overdue_udhar, get_overview, get_sync_log

st.set_page_config(page_title="Overview", page_icon="📊", layout="wide")
store_id = sidebar.setup()
if not store_id:
    st.info("👈 Enter your Store ID in the sidebar to view data.")
    st.stop()

st.title("Overview")

# KPI metrics
try:
    data = get_overview(store_id)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Today's Sales", f"₹{data['today_sales']:,.0f}")
    col2.metric(
        "Yesterday's Sales",
        f"₹{data['yesterday_sales']:,.0f}",
        delta=f"₹{data['today_sales'] - data['yesterday_sales']:,.0f}",
    )
    col3.metric("Pending Udhar", f"₹{data['pending_udhar_amount']:,.0f}")
    col4.metric("Udhar Entries", data["pending_udhar_count"])
    if data["last_sync_at"]:
        st.caption(f"Last Tally sync: {data['last_sync_at']}")
except Exception as e:
    st.error(f"Failed to load overview: {e}")

st.divider()

col_left, col_right = st.columns(2)

# Overdue Udhar table
with col_left:
    st.subheader("⚠️ Overdue Udhar")
    try:
        overdue = get_overdue_udhar(store_id)
        if overdue:
            df = pd.DataFrame(overdue)
            df.columns = ["Customer", "Amount (₹)", "Due Date", "Days Overdue"]
            df["Amount (₹)"] = df["Amount (₹)"].apply(lambda x: f"₹{x:,.0f}")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.success("No overdue entries.")
    except Exception as e:
        st.error(f"Error: {e}")

# Low stock table
with col_right:
    st.subheader("📦 Low Stock Items")
    try:
        low_stock = get_low_stock(store_id)
        if low_stock:
            df = pd.DataFrame(low_stock)
            df.columns = ["Item", "Unit", "Qty"]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.success("No low stock items.")
    except Exception as e:
        st.error(f"Error: {e}")

# Sync log
with st.expander("Sync History"):
    try:
        logs = get_sync_log(store_id)
        if logs:
            df = pd.DataFrame(logs)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No sync history yet.")
    except Exception as e:
        st.error(f"Error: {e}")
