"""Direct psycopg2 upsert to Supabase PostgreSQL — replaces cloud_client.py."""
import logging
from datetime import datetime

import psycopg2
import config as cfg

logger = logging.getLogger(__name__)


def _get_conn():
    return psycopg2.connect(cfg.SUPABASE_DB_URL)


def test_health() -> bool:
    """Verify we can reach the Supabase database."""
    try:
        conn = _get_conn()
        conn.close()
        logger.info("Supabase connection OK")
        return True
    except Exception as e:
        logger.error("Supabase connection failed: %s", e)
        return False


def push_sync(payload: dict) -> dict:
    """
    Upsert all Tally data directly into Supabase.
    Replicates the FastAPI sync.py logic using raw SQL.
    """
    store_id = cfg.STORE_ID
    from_date = payload.get("from_date")
    to_date = payload.get("to_date")
    sync_started_at = payload.get("sync_started_at", datetime.utcnow().isoformat())

    conn = _get_conn()
    cur = conn.cursor()
    sales_count = 0
    purchase_count = 0

    # Record sync start
    cur.execute(
        """
        INSERT INTO sync_logs (store_id, sync_started_at, status, from_date, to_date)
        VALUES (%s, %s, 'started', %s, %s)
        RETURNING id
        """,
        (store_id, sync_started_at, from_date, to_date),
    )
    sync_log_id = cur.fetchone()[0]
    conn.commit()

    try:
        # --- Sales vouchers ---
        for v in payload.get("sales_vouchers", []):
            cur.execute(
                """
                INSERT INTO sales_vouchers
                    (store_id, voucher_number, voucher_date, total_amount,
                     cgst_amount, sgst_amount, igst_amount, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (store_id, voucher_number) DO UPDATE SET
                    voucher_date   = EXCLUDED.voucher_date,
                    total_amount   = EXCLUDED.total_amount,
                    cgst_amount    = EXCLUDED.cgst_amount,
                    sgst_amount    = EXCLUDED.sgst_amount,
                    igst_amount    = EXCLUDED.igst_amount
                RETURNING id
                """,
                (
                    store_id, v["voucher_number"], v["voucher_date"],
                    v["total_amount"],
                    v.get("cgst_amount", 0), v.get("sgst_amount", 0), v.get("igst_amount", 0),
                ),
            )
            voucher_id = cur.fetchone()[0]

            cur.execute("DELETE FROM sales_voucher_items WHERE voucher_id = %s", (voucher_id,))
            for item in v.get("items", []):
                cur.execute(
                    """
                    INSERT INTO sales_voucher_items
                        (voucher_id, item_name, quantity, unit, rate, amount, gst_rate)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        voucher_id, item["item_name"],
                        item.get("quantity", 0), item.get("unit", ""),
                        item.get("rate", 0), item.get("amount", 0),
                        item.get("gst_rate", ""),
                    ),
                )
            sales_count += 1

        # --- Purchase vouchers ---
        for v in payload.get("purchase_vouchers", []):
            cur.execute(
                """
                INSERT INTO purchase_vouchers
                    (store_id, voucher_number, voucher_date, total_amount,
                     cgst_amount, sgst_amount, igst_amount, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (store_id, voucher_number) DO UPDATE SET
                    voucher_date   = EXCLUDED.voucher_date,
                    total_amount   = EXCLUDED.total_amount,
                    cgst_amount    = EXCLUDED.cgst_amount,
                    sgst_amount    = EXCLUDED.sgst_amount,
                    igst_amount    = EXCLUDED.igst_amount
                RETURNING id
                """,
                (
                    store_id, v["voucher_number"], v["voucher_date"],
                    v["total_amount"],
                    v.get("cgst_amount", 0), v.get("sgst_amount", 0), v.get("igst_amount", 0),
                ),
            )
            voucher_id = cur.fetchone()[0]

            cur.execute("DELETE FROM purchase_voucher_items WHERE voucher_id = %s", (voucher_id,))
            for item in v.get("items", []):
                cur.execute(
                    """
                    INSERT INTO purchase_voucher_items
                        (voucher_id, item_name, quantity, unit, rate, amount)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        voucher_id, item["item_name"],
                        item.get("quantity", 0), item.get("unit", ""),
                        item.get("rate", 0), item.get("amount", 0),
                    ),
                )
            purchase_count += 1

        # --- Stock items ---
        for s in payload.get("stock_items", []):
            cur.execute(
                """
                INSERT INTO stock_items
                    (store_id, item_name, item_group, unit,
                     closing_qty, closing_rate, closing_value, snapshot_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (store_id, item_name, snapshot_date) DO UPDATE SET
                    item_group    = EXCLUDED.item_group,
                    unit          = EXCLUDED.unit,
                    closing_qty   = EXCLUDED.closing_qty,
                    closing_rate  = EXCLUDED.closing_rate,
                    closing_value = EXCLUDED.closing_value
                """,
                (
                    store_id, s["item_name"], s.get("item_group", ""), s.get("unit", ""),
                    s.get("closing_qty", 0), s.get("closing_rate", 0),
                    s.get("closing_value", 0), s["snapshot_date"],
                ),
            )

        # --- Ledger entries ---
        for le in payload.get("ledger_entries", []):
            cur.execute(
                """
                INSERT INTO ledger_entries
                    (store_id, ledger_group, closing_balance, snapshot_date)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (store_id, ledger_group, snapshot_date) DO UPDATE SET
                    closing_balance = EXCLUDED.closing_balance
                """,
                (
                    store_id, le["ledger_group"],
                    le.get("closing_balance", 0), le["snapshot_date"],
                ),
            )

        # --- Payment entries ---
        for p in payload.get("payment_entries", []):
            cur.execute(
                """
                INSERT INTO payment_entries
                    (store_id, voucher_number, voucher_date, payment_type,
                     bank_or_cash, amount, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (store_id, voucher_number) DO UPDATE SET
                    voucher_date = EXCLUDED.voucher_date,
                    payment_type = EXCLUDED.payment_type,
                    bank_or_cash = EXCLUDED.bank_or_cash,
                    amount       = EXCLUDED.amount
                """,
                (
                    store_id, p["voucher_number"], p["voucher_date"],
                    p["payment_type"], p.get("bank_or_cash", ""), p.get("amount", 0),
                ),
            )

        conn.commit()

        # Mark sync success
        cur.execute(
            """
            UPDATE sync_logs
            SET status='success', sync_ended_at=NOW(),
                sales_count=%s, purchase_count=%s
            WHERE id=%s
            """,
            (sales_count, purchase_count, sync_log_id),
        )
        conn.commit()

        logger.info("Sync complete — %d sales, %d purchases", sales_count, purchase_count)
        return {"status": "success", "sales_count": sales_count, "purchase_count": purchase_count}

    except Exception as e:
        conn.rollback()
        logger.error("Sync failed: %s", e)
        try:
            cur.execute(
                "UPDATE sync_logs SET status='failed', sync_ended_at=NOW(), error_message=%s WHERE id=%s",
                (str(e), sync_log_id),
            )
            conn.commit()
        except Exception:
            pass
        raise

    finally:
        cur.close()
        conn.close()
