import logging
from datetime import datetime, timedelta
from collections import defaultdict

import pandas as pd
import numpy as np

from app.services import erpnext_service
from app.config import settings

logger = logging.getLogger(__name__)


def get_dashboard_summary() -> dict:
    """Get overall dashboard summary metrics."""
    items = erpnext_service.get_all_items()
    stock_levels = erpnext_service.get_stock_levels()

    stock_map = {s["item_code"]: s for s in stock_levels}

    total_items = len(items)
    total_stock_value = sum(
        s.get("actual_qty", 0) * s.get("valuation_rate", 0) for s in stock_levels
    )

    low_stock_count = 0
    out_of_stock_count = 0
    for item in items:
        code = item["name"]
        reorder_level = float(item.get("reorder_level") or 0)
        actual_qty = float(stock_map.get(code, {}).get("actual_qty", 0))
        if actual_qty <= 0:
            out_of_stock_count += 1
        elif reorder_level > 0 and actual_qty <= reorder_level:
            low_stock_count += 1

    return {
        "total_items": total_items,
        "total_stock_value": round(total_stock_value, 2),
        "low_stock_count": low_stock_count,
        "out_of_stock_count": out_of_stock_count,
    }


def get_reorder_alerts() -> list[dict]:
    """Identify items that have fallen below their reorder level."""
    items = erpnext_service.get_all_items()
    stock_levels = erpnext_service.get_stock_levels()

    stock_map = {s["item_code"]: float(s.get("actual_qty", 0)) for s in stock_levels}

    alerts = []
    for item in items:
        reorder_level = float(item.get("reorder_level") or 0)
        if reorder_level <= 0:
            continue

        actual_qty = stock_map.get(item["name"], 0)
        if actual_qty <= reorder_level:
            alerts.append({
                "item_code": item["name"],
                "item_name": item.get("item_name", ""),
                "current_qty": actual_qty,
                "reorder_level": reorder_level,
                "deficit": round(reorder_level - actual_qty, 2),
            })

    alerts.sort(key=lambda x: x["deficit"], reverse=True)
    return alerts


def get_dead_stock(days: int = 90) -> list[dict]:
    """Identify items with no movement in the specified number of days."""
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    items = erpnext_service.get_all_items()
    stock_levels = erpnext_service.get_stock_levels()
    ledger_entries = erpnext_service.get_stock_ledger_entries(from_date=cutoff_date)

    # Items that had recent movement
    active_items = {entry["item_code"] for entry in ledger_entries}

    stock_map = {s["item_code"]: float(s.get("actual_qty", 0)) for s in stock_levels}

    dead_stock = []
    for item in items:
        code = item["name"]
        qty = stock_map.get(code, 0)
        if qty > 0 and code not in active_items:
            dead_stock.append({
                "item_code": code,
                "item_name": item.get("item_name", ""),
                "current_qty": qty,
                "days_inactive": days,
            })

    return dead_stock


def get_demand_forecast(item_code: str, periods: int = 4) -> dict:
    """Forecast demand for an item using simple moving average."""
    to_date = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")

    ledger_entries = erpnext_service.get_stock_ledger_entries(
        item_code=item_code, from_date=from_date, to_date=to_date
    )

    # Group outward quantities by week
    weekly_demand = defaultdict(float)
    for entry in ledger_entries:
        qty = float(entry.get("actual_qty", 0))
        if qty < 0:  # Outward movement = demand
            date = datetime.strptime(entry["posting_date"], "%Y-%m-%d")
            week_key = date.strftime("%Y-W%W")
            weekly_demand[week_key] += abs(qty)

    if not weekly_demand:
        return {
            "item_code": item_code,
            "historical": [],
            "forecast": [],
            "avg_weekly_demand": 0,
        }

    # Sort by week
    sorted_weeks = sorted(weekly_demand.keys())
    demands = [weekly_demand[w] for w in sorted_weeks]

    # Simple moving average (window = min(4, len))
    window = min(4, len(demands))
    sma = np.convolve(demands, np.ones(window) / window, mode="valid").tolist()
    last_avg = sma[-1] if sma else 0

    # Forecast next N periods
    forecast = [round(last_avg, 2)] * periods

    return {
        "item_code": item_code,
        "historical": [
            {"week": w, "demand": round(weekly_demand[w], 2)} for w in sorted_weeks
        ],
        "forecast": [
            {"period": i + 1, "predicted_demand": f} for i, f in enumerate(forecast)
        ],
        "avg_weekly_demand": round(last_avg, 2),
    }


def get_sales_velocity(days: int = 30) -> list[dict]:
    """Calculate sales velocity (items sold per day) for all items."""
    from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    to_date = datetime.now().strftime("%Y-%m-%d")

    ledger_entries = erpnext_service.get_stock_ledger_entries(
        from_date=from_date, to_date=to_date
    )

    # Sum outward quantities by item
    item_sales = defaultdict(float)
    for entry in ledger_entries:
        qty = float(entry.get("actual_qty", 0))
        if qty < 0:
            item_sales[entry["item_code"]] += abs(qty)

    velocity = []
    for item_code, total_sold in item_sales.items():
        velocity.append({
            "item_code": item_code,
            "total_sold": round(total_sold, 2),
            "daily_avg": round(total_sold / days, 2),
            "period_days": days,
        })

    velocity.sort(key=lambda x: x["total_sold"], reverse=True)
    return velocity
