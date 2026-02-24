"""Supabase PostgreSQL connection helper for Streamlit."""
import psycopg2
import streamlit as st


def get_connection():
    """Return a new psycopg2 connection using the DB URL from Streamlit secrets."""
    return psycopg2.connect(st.secrets["SUPABASE_DB_URL"])


def run_query(sql: str, params=None) -> list[dict]:
    """Execute a SELECT query and return rows as a list of dicts."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()
