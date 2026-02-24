"""Shared sidebar component — import and call setup() at the top of every page."""
import streamlit as st


def setup() -> str | None:
    """Render store selector in the sidebar. Returns store_id or None."""
    with st.sidebar:
        st.title("🏪 POS Dashboard")
        st.divider()
        store_input = st.text_input(
            "Store ID",
            value=st.session_state.get("store_id", ""),
            placeholder="e.g. STORE001",
        )
        if st.button("Connect", type="primary"):
            if store_input.strip():
                st.session_state.store_id = store_input.strip().upper()
                st.rerun()
            else:
                st.error("Enter a Store ID")

        if st.session_state.get("store_id"):
            st.success(f"✓ {st.session_state.store_id}")
            if st.button("Disconnect"):
                del st.session_state["store_id"]
                st.rerun()

    return st.session_state.get("store_id")
