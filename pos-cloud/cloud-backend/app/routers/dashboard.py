from fastapi import APIRouter, Query
from app.services import tally_analytics as ta

router = APIRouter()


@router.get("/overview")
def overview(store_id: str = Query(...)):
    return ta.get_overview(store_id)


@router.get("/sales-trend")
def sales_trend(store_id: str = Query(...), period: str = Query(default="weekly")):
    return {"data": ta.get_sales_trend(store_id, period)}


@router.get("/top-items")
def top_items(store_id: str = Query(...), period: str = Query(default="weekly"), limit: int = Query(default=5)):
    return ta.get_top_items(store_id, period, limit)


@router.get("/cash-flow")
def cash_flow(store_id: str = Query(...), period: str = Query(default="monthly")):
    return {"data": ta.get_cash_flow(store_id, period)}


@router.get("/stock-snapshot")
def stock_snapshot(store_id: str = Query(...)):
    return {"data": ta.get_stock_snapshot(store_id)}


@router.get("/low-stock")
def low_stock(store_id: str = Query(...)):
    return {"data": ta.get_low_stock(store_id)}


@router.get("/overdue-udhar")
def overdue_udhar(store_id: str = Query(...)):
    return {"data": ta.get_overdue_udhar(store_id)}


@router.get("/sync-log")
def sync_log(store_id: str = Query(...), limit: int = Query(default=10)):
    return {"data": ta.get_sync_log(store_id, limit)}
