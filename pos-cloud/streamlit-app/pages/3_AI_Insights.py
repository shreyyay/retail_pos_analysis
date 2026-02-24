"""AI Insights page — pre-built insight cards + free-form chat."""
import streamlit as st

import sidebar
from llm import ask_insight, get_insight_cards

st.set_page_config(page_title="AI Insights", page_icon="🤖", layout="wide")
store_id = sidebar.setup()
if not store_id:
    st.info("👈 Enter your Store ID in the sidebar to view data.")
    st.stop()

st.title("AI Insights")

CARD_ICONS = {
    "sales_summary": "📊",
    "top_items": "🏆",
    "least_items": "📉",
    "cash_flow": "💰",
    "overdue_udhar": "⚠️",
    "low_stock": "📦",
}

# Pre-built insight cards
st.subheader("Business Summary Cards")
period = st.selectbox(
    "Period",
    ["daily", "weekly", "monthly", "quarterly", "half-yearly", "annually"],
    index=1,
    key="insight_period",
)

if st.button("Generate Insights", type="primary"):
    with st.spinner("Asking AI — this may take 20-30 seconds..."):
        try:
            cards = get_insight_cards(store_id, period)
            cols = st.columns(2)
            for i, card in enumerate(cards):
                icon = CARD_ICONS.get(card["type"], "💡")
                title = card["type"].replace("_", " ").title()
                with cols[i % 2]:
                    st.info(f"**{icon} {title}**\n\n{card['answer']}")
        except Exception as e:
            st.error(f"Error generating insights: {e}")

st.divider()

# Free-form chat
st.subheader("Ask Your Business Anything")
st.caption("Examples: 'What were my top products last week?' · 'How much udhar is overdue?' · 'Compare cash inflow vs outflow this month'")

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# Render chat history
for msg in st.session_state.chat_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# New question
if question := st.chat_input("Ask about your business..."):
    st.session_state.chat_messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                result = ask_insight(question, store_id)
                answer = result["answer"]
            except Exception as e:
                answer = f"Error: {e}"
        st.markdown(answer)
        st.session_state.chat_messages.append({"role": "assistant", "content": answer})

if st.session_state.chat_messages:
    if st.button("Clear chat"):
        st.session_state.chat_messages = []
        st.rerun()
