from datetime import datetime

from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey,
    Integer, Numeric, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Store(Base):
    __tablename__ = "stores"
    store_id = Column(String(64), primary_key=True)
    store_name = Column(String(255), nullable=False)
    api_key_hash = Column(String(128), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SalesVoucher(Base):
    __tablename__ = "sales_vouchers"
    id = Column(Integer, primary_key=True)
    store_id = Column(String(64), ForeignKey("stores.store_id"), nullable=False, index=True)
    voucher_number = Column(String(128), nullable=False)
    voucher_date = Column(Date, nullable=False, index=True)
    total_amount = Column(Numeric(12, 2), nullable=False)
    cgst_amount = Column(Numeric(10, 2), default=0)
    sgst_amount = Column(Numeric(10, 2), default=0)
    igst_amount = Column(Numeric(10, 2), default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("store_id", "voucher_number"),)
    items = relationship("SalesVoucherItem", back_populates="voucher", cascade="all, delete-orphan")


class SalesVoucherItem(Base):
    __tablename__ = "sales_voucher_items"
    id = Column(Integer, primary_key=True)
    voucher_id = Column(Integer, ForeignKey("sales_vouchers.id"), nullable=False, index=True)
    item_name = Column(String(255), nullable=False)
    quantity = Column(Numeric(10, 3), default=0)
    unit = Column(String(32), default="")
    rate = Column(Numeric(10, 2), default=0)
    amount = Column(Numeric(12, 2), default=0)
    gst_rate = Column(String(16), default="")
    voucher = relationship("SalesVoucher", back_populates="items")


class PurchaseVoucher(Base):
    __tablename__ = "purchase_vouchers"
    id = Column(Integer, primary_key=True)
    store_id = Column(String(64), ForeignKey("stores.store_id"), nullable=False, index=True)
    voucher_number = Column(String(128), nullable=False)
    voucher_date = Column(Date, nullable=False, index=True)
    total_amount = Column(Numeric(12, 2), nullable=False)
    cgst_amount = Column(Numeric(10, 2), default=0)
    sgst_amount = Column(Numeric(10, 2), default=0)
    igst_amount = Column(Numeric(10, 2), default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("store_id", "voucher_number"),)
    items = relationship("PurchaseVoucherItem", back_populates="voucher", cascade="all, delete-orphan")


class PurchaseVoucherItem(Base):
    __tablename__ = "purchase_voucher_items"
    id = Column(Integer, primary_key=True)
    voucher_id = Column(Integer, ForeignKey("purchase_vouchers.id"), nullable=False, index=True)
    item_name = Column(String(255), nullable=False)
    quantity = Column(Numeric(10, 3), default=0)
    unit = Column(String(32), default="")
    rate = Column(Numeric(10, 2), default=0)
    amount = Column(Numeric(12, 2), default=0)
    voucher = relationship("PurchaseVoucher", back_populates="items")


class StockItem(Base):
    __tablename__ = "stock_items"
    id = Column(Integer, primary_key=True)
    store_id = Column(String(64), ForeignKey("stores.store_id"), nullable=False, index=True)
    item_name = Column(String(255), nullable=False)
    item_group = Column(String(255), default="")
    unit = Column(String(32), default="")
    closing_qty = Column(Numeric(12, 3), default=0)
    closing_rate = Column(Numeric(10, 2), default=0)
    closing_value = Column(Numeric(14, 2), default=0)
    snapshot_date = Column(Date, nullable=False)
    __table_args__ = (UniqueConstraint("store_id", "item_name", "snapshot_date"),)


class LedgerEntry(Base):
    """Group-level ledger balances only — no individual party names."""
    __tablename__ = "ledger_entries"
    id = Column(Integer, primary_key=True)
    store_id = Column(String(64), ForeignKey("stores.store_id"), nullable=False, index=True)
    ledger_group = Column(String(255), nullable=False)
    closing_balance = Column(Numeric(14, 2), default=0)
    snapshot_date = Column(Date, nullable=False)
    __table_args__ = (UniqueConstraint("store_id", "ledger_group", "snapshot_date"),)


class PaymentEntry(Base):
    """Cash/Bank payment type and amount only — no party names."""
    __tablename__ = "payment_entries"
    id = Column(Integer, primary_key=True)
    store_id = Column(String(64), ForeignKey("stores.store_id"), nullable=False, index=True)
    voucher_number = Column(String(128), nullable=False)
    voucher_date = Column(Date, nullable=False, index=True)
    payment_type = Column(String(32), nullable=False)   # Payment | Receipt
    bank_or_cash = Column(String(32), default="")
    amount = Column(Numeric(12, 2), default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("store_id", "voucher_number"),)


class SyncLog(Base):
    __tablename__ = "sync_logs"
    id = Column(Integer, primary_key=True)
    store_id = Column(String(64), ForeignKey("stores.store_id"), nullable=False, index=True)
    sync_started_at = Column(DateTime, nullable=False)
    sync_ended_at = Column(DateTime, nullable=True)
    status = Column(String(32), nullable=False, default="started")  # started|success|partial|failed
    from_date = Column(Date, nullable=True)
    to_date = Column(Date, nullable=True)
    sales_count = Column(Integer, default=0)
    purchase_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
