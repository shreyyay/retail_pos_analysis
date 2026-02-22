"""Nightly Tally → Cloud sync orchestrator. Run via run_sync.bat."""
import logging, os, sys
from datetime import date, datetime, timedelta
import cloud_client, config as cfg, sync_state, tally_client, transformer

_LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(_LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s – %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(_LOG_DIR, "sync.log"), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("tally_connector")


def run():
    logger.info("=" * 60)
    logger.info("Tally Connector starting — store: %s", cfg.STORE_ID)

    from_date = sync_state.get_from_date()
    to_date = date.today()
    max_to = from_date + timedelta(days=cfg.MAX_DAYS_PER_SYNC - 1)
    if to_date > max_to:
        logger.warning("Date range capped to %d days", cfg.MAX_DAYS_PER_SYNC)
        to_date = max_to

    if from_date > to_date:
        logger.info("Nothing to sync. Exiting."); return

    logger.info("Sync window: %s → %s", from_date, to_date)

    if not cloud_client.test_health():
        logger.error("Cloud API unreachable. Aborting."); sys.exit(1)

    try:
        sales_xml     = tally_client.fetch_sales_vouchers(from_date, to_date)
        purchase_xml  = tally_client.fetch_purchase_vouchers(from_date, to_date)
        stock_xml     = tally_client.fetch_stock_summary(to_date)
        ledger_xml    = tally_client.fetch_ledger_balances(to_date)
        payment_xml   = tally_client.fetch_payment_vouchers(from_date, to_date)
        receipt_xml   = tally_client.fetch_receipt_vouchers(from_date, to_date)
    except Exception as e:
        logger.error("Tally fetch failed: %s", e); sys.exit(1)

    sales_v    = transformer.parse_sales_vouchers(sales_xml)
    purchase_v = transformer.parse_purchase_vouchers(purchase_xml)
    stock      = transformer.parse_stock_summary(stock_xml, to_date)
    ledger     = transformer.parse_ledger_balances(ledger_xml, to_date)
    payments   = transformer.parse_payment_receipts(payment_xml, receipt_xml)

    logger.info("Parsed: %d sales, %d purchases, %d stock, %d ledger, %d payments",
                len(sales_v), len(purchase_v), len(stock), len(ledger), len(payments))

    payload = {
        "from_date": from_date.isoformat(), "to_date": to_date.isoformat(),
        "connector_version": "1.0.0",
        "sync_started_at": datetime.utcnow().isoformat(),
        "sales_vouchers": sales_v, "purchase_vouchers": purchase_v,
        "stock_items": stock, "ledger_entries": ledger, "payment_entries": payments,
    }

    try:
        result = cloud_client.push_sync(payload)
        logger.info("Cloud response: %s", result)
    except Exception as e:
        logger.error("Push failed: %s", e); sys.exit(1)

    sync_state.save_sync_date(to_date)
    logger.info("Sync complete. Last sync: %s", to_date)
    logger.info("=" * 60)


if __name__ == "__main__":
    run()
