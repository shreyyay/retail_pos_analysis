"""Sales Trends page — charts for sales, top items, and cash flow."""
import pandas as pd
import plotly.express as px
import streamlit as st

import sidebar
from analytics import get_cash_flow, get_sales_trend, get_top_items

st.set_page_config(page_title="Sales Trends", page_icon="📈", layout="wide")
store_id = sidebar.setup()
if not store_id:
    st.info("👈 Enter your Store ID in the sidebar to view data.")
    st.stop()

st.title("Sales Trends")

period = st.selectbox(
    "Period",
    ["daily", "weekly", "monthly", "quarterly", "half-yearly", "annually"],
    index=1,
)

st.divider()

# Sales trend line chart
st.subheader("Sales Over Time")
try:
    trend = get_sales_trend(store_id, period)
    if trend:
        df = pd.DataFrame(trend)
        fig = px.line(
            df, x="sale_date", y="total_sales",
            labels={"sale_date": "Date", "total_sales": "Sales (₹)"},
            markers=True,
        )
        fig.update_traces(line_color="#636EFA")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No sales data for this period.")
except Exception as e:
    st.error(f"Error loading sales trend: {e}")

# Top / Least items
st.subheader("Item Performance")
try:
    items = get_top_items(store_id, period)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Top 5 Items by Revenue**")
        if items["top"]:
            df = pd.DataFrame(items["top"])
            fig = px.bar(
                df, x="item_name", y="revenue",
                labels={"item_name": "Item", "revenue": "Revenue (₹)"},
                color_discrete_sequence=["#00CC96"],
            )
            fig.update_layout(xaxis_tickangle=-30)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data.")

    with col2:
        st.markdown("**5 Least Selling Items**")
        if items["least"]:
            df = pd.DataFrame(items["least"])
            fig = px.bar(
                df, x="item_name", y="revenue",
                labels={"item_name": "Item", "revenue": "Revenue (₹)"},
                color_discrete_sequence=["#EF553B"],
            )
            fig.update_layout(xaxis_tickangle=-30)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data.")
except Exception as e:
    st.error(f"Error loading item data: {e}")

# Cash flow
st.subheader("Cash Flow")
try:
    flow = get_cash_flow(store_id, period)
    if flow:
        df = pd.DataFrame(flow)
        fig = px.area(
            df, x="flow_date", y=["total_in", "total_out"],
            labels={"flow_date": "Date", "value": "Amount (₹)", "variable": ""},
            color_discrete_map={"total_in": "#00CC96", "total_out": "#EF553B"},
        )
        fig.update_traces(selector=dict(name="total_in"), name="Sales In")
        fig.update_traces(selector=dict(name="total_out"), name="Purchases Out")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No cash flow data for this period.")
except Exception as e:
    st.error(f"Error loading cash flow: {e}")
