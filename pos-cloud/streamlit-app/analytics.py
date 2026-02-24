"""Pre-built SQL analytics queries — copy of tally_analytics.py adapted for Streamlit."""
from datetime import date, timedelta

from db import get_connection

PERIOD_DAYS = {
    "daily": 1,
    "weekly": 7,
    "monthly": 30,
    "quarterly": 90,
    "half-yearly": 180,
    "annually": 365,
}


def _days(period: str) -> int:
    return PERIOD_DAYS.get(period, 7)


def get_overview(store_id: str) -> dict:
    conn = get_connection()
    cur = conn.cursor()
    try:
        today = date.today()
        yesterday = today - timedelta(days=1)

        cur.execute(
            "SELECT COALESCE(SUM(total_amount),0) FROM sales_vouchers "
            "WHERE store_id=%s AND voucher_date=%s",
            (store_id, today),
        )
        today_sales = float(cur.fetchone()[0])

        cur.execute(
            "SELECT COALESCE(SUM(total_amount),0) FROM sales_vouchers "
            "WHERE store_id=%s AND voucher_date=%s",
            (store_id, yesterday),
        )
        yesterday_sales = float(cur.fetchone()[0])

        cur.execute(
            "SELECT COALESCE(SUM(amount),0), COUNT(*) FROM udhar "
            "WHERE store_id=%s AND status='Pending'",
            (store_id,),
        )
        row = cur.fetchone()
        pending_amount, pending_count = float(row[0]), int(row[1])

        cur.execute(
            "SELECT sync_ended_at FROM sync_logs WHERE store_id=%s AND status='success' "
            "ORDER BY sync_ended_at DESC LIMIT 1",
            (store_id,),
        )
        row = cur.fetchone()
        last_sync = row[0].isoformat() if row and row[0] else None

        return {
            "today_sales": today_sales,
            "yesterday_sales": yesterday_sales,
            "pending_udhar_amount": pending_amount,
            "pending_udhar_count": pending_count,
            "last_sync_at": last_sync,
        }
    finally:
        cur.close()
        conn.close()


def get_sales_trend(store_id: str, period: str) -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    try:
        days = _days(period)
        cur.execute(
            """
            SELECT voucher_date::text AS sale_date,
                   COALESCE(SUM(total_amount), 0) AS total_sales
            FROM sales_vouchers
            WHERE store_id = %s AND voucher_date >= CURRENT_DATE - %s
            GROUP BY voucher_date
            ORDER BY voucher_date
            """,
            (store_id, days),
        )
        return [{"sale_date": r[0], "total_sales": float(r[1])} for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()


def get_top_items(store_id: str, period: str, limit: int = 5) -> dict:
    conn = get_connection()
    cur = conn.cursor()
    try:
        days = _days(period)
        sql = """
            SELECT i.item_name, COALESCE(SUM(i.amount), 0) AS revenue
            FROM sales_voucher_items i
            JOIN sales_vouchers v ON v.id = i.voucher_id
            WHERE v.store_id = %s AND v.voucher_date >= CURRENT_DATE - %s
            GROUP BY i.item_name
            ORDER BY revenue {order}
            LIMIT %s
        """
        cur.execute(sql.format(order="DESC"), (store_id, days, limit))
        top = [{"item_name": r[0], "revenue": float(r[1])} for r in cur.fetchall()]

        cur.execute(sql.format(order="ASC"), (store_id, days, limit))
        least = [{"item_name": r[0], "revenue": float(r[1])} for r in cur.fetchall()]

        return {"top": top, "least": least}
    finally:
        cur.close()
        conn.close()


def get_cash_flow(store_id: str, period: str) -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    try:
        days = _days(period)
        cur.execute(
            """
            SELECT d::date AS flow_date,
                COALESCE(s.total_in, 0) AS total_in,
                COALESCE(p.total_out, 0) AS total_out
            FROM generate_series(
                CURRENT_DATE - %s::int,
                CURRENT_DATE,
                '1 day'::interval
            ) AS d
            LEFT JOIN (
                SELECT voucher_date, SUM(total_amount) AS total_in
                FROM sales_vouchers WHERE store_id = %s
                GROUP BY voucher_date
            ) s ON s.voucher_date = d::date
            LEFT JOIN (
                SELECT voucher_date, SUM(total_amount) AS total_out
                FROM purchase_vouchers WHERE store_id = %s
                GROUP BY voucher_date
            ) p ON p.voucher_date = d::date
            ORDER BY d
            """,
            (days, store_id, store_id),
        )
        return [
            {"flow_date": str(r[0]), "total_in": float(r[1]), "total_out": float(r[2])}
            for r in cur.fetchall()
        ]
    finally:
        cur.close()
        conn.close()


def get_stock_snapshot(store_id: str) -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT item_name, item_group, unit, closing_qty, closing_rate, closing_value
            FROM stock_items
            WHERE store_id = %s
              AND snapshot_date = (
                  SELECT MAX(snapshot_date) FROM stock_items WHERE store_id = %s
              )
            ORDER BY closing_value DESC
            LIMIT 100
            """,
            (store_id, store_id),
        )
        cols = ["item_name", "item_group", "unit", "closing_qty", "closing_rate", "closing_value"]
        return [dict(zip(cols, (r[0], r[1], r[2], float(r[3]), float(r[4]), float(r[5])))) for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()


def get_low_stock(store_id: str) -> list[dict]:
    """Return items in the bottom 20% by closing_qty from the latest snapshot."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            WITH latest AS (
                SELECT item_name, unit, closing_qty
                FROM stock_items
                WHERE store_id = %s
                  AND snapshot_date = (
                      SELECT MAX(snapshot_date) FROM stock_items WHERE store_id = %s
                  )
            ),
            ranked AS (
                SELECT *, PERCENT_RANK() OVER (ORDER BY closing_qty) AS prank
                FROM latest
            )
            SELECT item_name, unit, closing_qty
            FROM ranked
            WHERE prank <= 0.20
            ORDER BY closing_qty ASC
            LIMIT 50
            """,
            (store_id, store_id),
        )
        return [{"item_name": r[0], "unit": r[1], "closing_qty": float(r[2])} for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()


def get_overdue_udhar(store_id: str) -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT customer_name, amount, due_date,
                   (CURRENT_DATE - due_date) AS days_overdue
            FROM udhar
            WHERE store_id = %s AND status = 'Pending' AND due_date < CURRENT_DATE
            ORDER BY days_overdue DESC
            LIMIT 50
            """,
            (store_id,),
        )
        return [
            {"customer_name": r[0], "amount": float(r[1]),
             "due_date": str(r[2]), "days_overdue": int(r[3])}
            for r in cur.fetchall()
        ]
    finally:
        cur.close()
        conn.close()


def get_sync_log(store_id: str, limit: int = 10) -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT status, sync_started_at, sync_ended_at,
                   from_date, to_date, sales_count, purchase_count, error_message
            FROM sync_logs WHERE store_id = %s
            ORDER BY sync_started_at DESC LIMIT %s
            """,
            (store_id, limit),
        )
        cols = ["status", "sync_started_at", "sync_ended_at",
                "from_date", "to_date", "sales_count", "purchase_count", "error_message"]
        return [dict(zip(cols, [str(v) if v is not None else None for v in r])) for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()
