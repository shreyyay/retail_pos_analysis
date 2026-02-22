"""LLM text-to-SQL pipeline using Groq + Llama 3.1 70B."""
import re
import logging

from groq import Groq

from app.config import settings
from app.database import get_raw_connection
from app.services.tally_analytics import PERIOD_DAYS

logger = logging.getLogger(__name__)

# Columns exposed to LLM — omits party_name, phone, supplier_name, store_id, narration
LLM_SCHEMA = """
Tables available (store data is pre-filtered — do NOT add WHERE store_id clauses):

sales_vouchers(id, voucher_number, voucher_date, total_amount, cgst_amount, sgst_amount, igst_amount)
sales_voucher_items(id, voucher_id, item_name, quantity, unit, rate, amount, gst_rate)
purchase_vouchers(id, voucher_number, voucher_date, total_amount, cgst_amount, sgst_amount, igst_amount)
purchase_voucher_items(id, voucher_id, item_name, quantity, unit, rate, amount)
stock_items(id, item_name, item_group, unit, closing_qty, closing_rate, closing_value, snapshot_date)
ledger_entries(id, ledger_group, closing_balance, snapshot_date)
payment_entries(id, voucher_number, voucher_date, payment_type, bank_or_cash, amount)
udhar(id, customer_name, amount, date_given, due_date, status)
followup(id, customer_name, salesperson, notes, followup_date, next_followup_date, status)
"""

SAFETY_RULES = """
Rules:
- Return ONLY a valid PostgreSQL SELECT statement, nothing else
- No semicolons, no multiple statements
- LIMIT results to 100 rows maximum
- No INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, GRANT
- If the question cannot be answered with the available tables, return exactly: CANNOT_ANSWER
"""

CARD_QUESTIONS = {
    "sales_summary": "What is the total sales revenue, number of invoices, and average invoice value for the last {DAYS} days?",
    "top_items": "List the top 5 items by revenue for the last {DAYS} days with their quantities sold.",
    "least_items": "List the 5 least selling items by revenue for the last {DAYS} days.",
    "cash_flow": "What is the total cash inflow (sales) and total purchases outflow for the last {DAYS} days, and the net difference?",
    "overdue_udhar": "How many Udhar entries are overdue (past due date and still Pending)? What is the total overdue amount?",
    "low_stock": "Which items have the lowest stock quantity? List up to 10 items with their current quantity and unit.",
}

PERIOD_SENSITIVE = {"sales_summary", "top_items", "least_items", "cash_flow"}


def _validate_sql(sql: str) -> bool:
    forbidden = re.compile(
        r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT|EXEC|EXECUTE)\b",
        re.IGNORECASE,
    )
    return not forbidden.search(sql)


def _inject_store_filter(sql: str, store_id: str) -> str:
    """Wrap every table reference with a store-filtered subquery."""
    tables = [
        "sales_vouchers", "sales_voucher_items",
        "purchase_vouchers", "purchase_voucher_items",
        "stock_items", "ledger_entries", "payment_entries",
        "udhar", "followup",
    ]
    result = sql
    for table in tables:
        pattern = rf"\b{table}\b"
        replacement = f"(SELECT * FROM {table} WHERE store_id = '{store_id}') AS {table}"
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result


def ask_insight(question: str, store_id: str) -> dict:
    client = Groq(api_key=settings.GROQ_API_KEY)

    # Step 1: question → SQL
    sql_prompt = (
        f"{LLM_SCHEMA}\n{SAFETY_RULES}\n\n"
        f"Question: {question}\n\nSQL:"
    )
    sql_msg = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        max_tokens=512,
        messages=[{"role": "user", "content": sql_prompt}],
    )
    raw_sql = sql_msg.choices[0].message.content.strip()

    if raw_sql.upper() == "CANNOT_ANSWER":
        return {"question": question, "answer": "I can't answer that with the available data.", "sql_used": None, "data": []}

    if not _validate_sql(raw_sql):
        return {"question": question, "answer": "Query was blocked for safety reasons.", "sql_used": None, "data": []}

    safe_sql = _inject_store_filter(raw_sql, store_id)

    # Step 2: Execute SQL
    conn = get_raw_connection()
    cur = conn.cursor()
    rows, columns = [], []
    try:
        cur.execute(safe_sql)
        columns = [d[0] for d in cur.description]
        rows = [dict(zip(columns, [str(v) if v is not None else None for v in r])) for r in cur.fetchall()]
    except Exception as e:
        logger.error("SQL execution error: %s | SQL: %s", e, safe_sql)
        return {"question": question, "answer": f"SQL error: {e}", "sql_used": raw_sql, "data": []}
    finally:
        cur.close()
        conn.close()

    # Step 3: data → natural language answer
    answer_prompt = (
        f"Question: {question}\n\n"
        f"Data (JSON):\n{rows[:20]}\n\n"
        "Provide a concise, friendly answer in 1-3 sentences. Use ₹ for currency. "
        "Round numbers sensibly. Refer to 'your store' not 'the store'."
    )
    ans_msg = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        max_tokens=300,
        messages=[{"role": "user", "content": answer_prompt}],
    )
    answer = ans_msg.choices[0].message.content.strip()

    return {"question": question, "answer": answer, "sql_used": raw_sql, "data": rows}


def get_insight_cards(store_id: str, period: str) -> list[dict]:
    days = PERIOD_DAYS.get(period, 7)
    cards = []
    for card_type, question_template in CARD_QUESTIONS.items():
        question = question_template.replace("{DAYS}", str(days))
        try:
            result = ask_insight(question, store_id)
            cards.append({
                "type": card_type,
                "period": period if card_type in PERIOD_SENSITIVE else "always",
                "question": question,
                "answer": result["answer"],
            })
        except Exception as e:
            logger.error("Card %s failed: %s", card_type, e)
            cards.append({"type": card_type, "period": period, "answer": "Data unavailable"})
    return cards
