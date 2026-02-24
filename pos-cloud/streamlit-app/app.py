"""Main entry point — store selector and home page."""
import streamlit as st
import sidebar

st.set_page_config(
    page_title="Retail POS Dashboard",
    page_icon="🏪",
    layout="wide",
)

store_id = sidebar.setup()

if not store_id:
    st.title("Welcome to POS Dashboard")
    st.info("👈 Enter your Store ID in the sidebar and click **Connect** to get started.")
    st.markdown("""
    ### Pages
    | Page | What it shows |
    |------|--------------|
    | **Overview** | Today's sales, pending udhar, low stock alert |
    | **Sales Trends** | Daily/weekly/monthly charts + top & least items |
    | **AI Insights** | Ask any question about your business in plain language |
    | **Udhar** | Track credit given to customers, mark as paid |
    | **Follow-up** | Manage customer follow-up tasks |
    """)
else:
    st.title(f"Dashboard — {store_id}")
    st.success("Connected! Select a page from the sidebar to begin.")

    # Quick summary on home page
    try:
        from analytics import get_overview
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
            st.caption(f"Last sync: {data['last_sync_at']}")
    except Exception as e:
        st.warning(f"Could not load overview data: {e}")
