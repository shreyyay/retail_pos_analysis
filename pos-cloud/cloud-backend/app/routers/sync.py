"""Receive Tally data from the local connector and upsert into PostgreSQL."""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.tally import (
    LedgerEntry, PaymentEntry, PurchaseVoucher, PurchaseVoucherItem,
    SalesVoucher, SalesVoucherItem, StockItem, SyncLog,
)
from app.services.auth import verify_sync_key

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Pydantic schemas for incoming payload ─────────────────────────────────────
class SalesItemIn(BaseModel):
    item_name: str
    quantity: float = 0
    unit: str = ""
    rate: float = 0
    amount: float = 0
    gst_rate: str = ""


class SalesVoucherIn(BaseModel):
    voucher_number: str
    voucher_date: str
    total_amount: float
    cgst_amount: float = 0
    sgst_amount: float = 0
    igst_amount: float = 0
    items: list[SalesItemIn] = []


class PurchaseItemIn(BaseModel):
    item_name: str
    quantity: float = 0
    unit: str = ""
    rate: float = 0
    amount: float = 0


class PurchaseVoucherIn(BaseModel):
    voucher_number: str
    voucher_date: str
    total_amount: float
    cgst_amount: float = 0
    sgst_amount: float = 0
    igst_amount: float = 0
    items: list[PurchaseItemIn] = []


class StockItemIn(BaseModel):
    item_name: str
    item_group: str = ""
    unit: str = ""
    closing_qty: float = 0
    closing_rate: float = 0
    closing_value: float = 0
    snapshot_date: str


class LedgerEntryIn(BaseModel):
    ledger_group: str
    closing_balance: float = 0
    snapshot_date: str


class PaymentEntryIn(BaseModel):
    voucher_number: str
    voucher_date: str
    payment_type: str
    bank_or_cash: str = ""
    amount: float = 0


class SyncPayload(BaseModel):
    from_date: str
    to_date: str
    connector_version: str = ""
    sync_started_at: Optional[str] = None
    sales_vouchers: list[SalesVoucherIn] = []
    purchase_vouchers: list[PurchaseVoucherIn] = []
    stock_items: list[StockItemIn] = []
    ledger_entries: list[LedgerEntryIn] = []
    payment_entries: list[PaymentEntryIn] = []


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.post("/health")
def health(store=Depends(verify_sync_key)):
    return {"status": "ok", "store_id": store.store_id}


@router.post("/")
def receive_sync(
    payload: SyncPayload,
    db: Session = Depends(get_db),
    store=Depends(verify_sync_key),
):
    store_id = store.store_id
    started_at = datetime.utcnow()
    sync_log = SyncLog(
        store_id=store_id,
        sync_started_at=started_at,
        status="started",
        from_date=payload.from_date,
        to_date=payload.to_date,
    )
    db.add(sync_log)
    db.flush()

    try:
        sales_count = _upsert_sales(db, store_id, payload.sales_vouchers)
        purchase_count = _upsert_purchases(db, store_id, payload.purchase_vouchers)
        _upsert_stock(db, store_id, payload.stock_items)
        _upsert_ledger(db, store_id, payload.ledger_entries)
        _upsert_payments(db, store_id, payload.payment_entries)

        sync_log.status = "success"
        sync_log.sync_ended_at = datetime.utcnow()
        sync_log.sales_count = sales_count
        sync_log.purchase_count = purchase_count
        db.commit()

        return {"status": "success", "sales": sales_count, "purchases": purchase_count}

    except Exception as e:
        db.rollback()
        sync_log.status = "failed"
        sync_log.error_message = str(e)[:500]
        sync_log.sync_ended_at = datetime.utcnow()
        db.add(sync_log)
        db.commit()
        logger.exception("Sync failed for store %s", store_id)
        raise


def _upsert_sales(db, store_id, vouchers):
    count = 0
    for v in vouchers:
        stmt = pg_insert(SalesVoucher).values(
            store_id=store_id,
            voucher_number=v.voucher_number,
            voucher_date=v.voucher_date,
            total_amount=v.total_amount,
            cgst_amount=v.cgst_amount,
            sgst_amount=v.sgst_amount,
            igst_amount=v.igst_amount,
        ).on_conflict_do_update(
            index_elements=["store_id", "voucher_number"],
            set_={"total_amount": v.total_amount, "voucher_date": v.voucher_date},
        ).returning(SalesVoucher.id)
        result = db.execute(stmt)
        voucher_id = result.scalar()

        # Delete old items and re-insert (simplest idempotent approach)
        db.query(SalesVoucherItem).filter(SalesVoucherItem.voucher_id == voucher_id).delete()
        for item in v.items:
            db.add(SalesVoucherItem(
                voucher_id=voucher_id,
                item_name=item.item_name,
                quantity=item.quantity,
                unit=item.unit,
                rate=item.rate,
                amount=item.amount,
                gst_rate=item.gst_rate,
            ))
        count += 1
    db.flush()
    return count


def _upsert_purchases(db, store_id, vouchers):
    count = 0
    for v in vouchers:
        stmt = pg_insert(PurchaseVoucher).values(
            store_id=store_id,
            voucher_number=v.voucher_number,
            voucher_date=v.voucher_date,
            total_amount=v.total_amount,
            cgst_amount=v.cgst_amount,
            sgst_amount=v.sgst_amount,
            igst_amount=v.igst_amount,
        ).on_conflict_do_update(
            index_elements=["store_id", "voucher_number"],
            set_={"total_amount": v.total_amount},
        ).returning(PurchaseVoucher.id)
        result = db.execute(stmt)
        voucher_id = result.scalar()
        db.query(PurchaseVoucherItem).filter(PurchaseVoucherItem.voucher_id == voucher_id).delete()
        for item in v.items:
            db.add(PurchaseVoucherItem(
                voucher_id=voucher_id, item_name=item.item_name,
                quantity=item.quantity, unit=item.unit, rate=item.rate, amount=item.amount,
            ))
        count += 1
    db.flush()
    return count


def _upsert_stock(db, store_id, items):
    for item in items:
        stmt = pg_insert(StockItem).values(
            store_id=store_id, item_name=item.item_name, item_group=item.item_group,
            unit=item.unit, closing_qty=item.closing_qty,
            closing_rate=item.closing_rate, closing_value=item.closing_value,
            snapshot_date=item.snapshot_date,
        ).on_conflict_do_update(
            index_elements=["store_id", "item_name", "snapshot_date"],
            set_={"closing_qty": item.closing_qty, "closing_value": item.closing_value},
        )
        db.execute(stmt)
    db.flush()


def _upsert_ledger(db, store_id, entries):
    for entry in entries:
        stmt = pg_insert(LedgerEntry).values(
            store_id=store_id, ledger_group=entry.ledger_group,
            closing_balance=entry.closing_balance, snapshot_date=entry.snapshot_date,
        ).on_conflict_do_update(
            index_elements=["store_id", "ledger_group", "snapshot_date"],
            set_={"closing_balance": entry.closing_balance},
        )
        db.execute(stmt)
    db.flush()


def _upsert_payments(db, store_id, entries):
    for entry in entries:
        stmt = pg_insert(PaymentEntry).values(
            store_id=store_id, voucher_number=entry.voucher_number,
            voucher_date=entry.voucher_date, payment_type=entry.payment_type,
            bank_or_cash=entry.bank_or_cash, amount=entry.amount,
        ).on_conflict_do_update(
            index_elements=["store_id", "voucher_number"],
            set_={"amount": entry.amount},
        )
        db.execute(stmt)
    db.flush()
