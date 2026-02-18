import logging
from typing import Optional

import requests

from app.config import settings

logger = logging.getLogger(__name__)


def _get_headers() -> dict:
    return {
        "Authorization": f"token {settings.ERPNEXT_API_KEY}:{settings.ERPNEXT_API_SECRET}",
        "Content-Type": "application/json",
    }


def _api_url(endpoint: str) -> str:
    return f"{settings.ERPNEXT_URL}{endpoint}"


# --- Stock Entry ---


def create_stock_entry(
    items: list[dict],
    supplier: str,
    invoice_no: str,
    entry_type: str = "Material Receipt",
    warehouse: str = "",
) -> dict:
    """Create a Stock Entry in ERPNext (Material Receipt or Material Issue)."""
    if not warehouse:
        warehouse = settings.DEFAULT_WAREHOUSE

    warehouse_key = "t_warehouse" if entry_type == "Material Receipt" else "s_warehouse"

    stock_entry = {
        "doctype": "Stock Entry",
        "stock_entry_type": entry_type,
        "supplier": supplier if entry_type == "Material Receipt" else "",
        "items": [
            {
                "item_code": item["item_code"],
                "qty": item["qty"],
                "basic_rate": item["basic_rate"],
                warehouse_key: warehouse,
            }
            for item in items
        ],
    }

    response = requests.post(
        _api_url("/api/resource/Stock Entry"),
        json=stock_entry,
        headers=_get_headers(),
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    entry_name = data.get("data", {}).get("name", "")
    return {
        "success": True,
        "message": f"Stock Entry {entry_name} created successfully",
        "entry_name": entry_name,
        "entry_url": f"{settings.ERPNEXT_URL}/app/stock-entry/{entry_name}",
    }


# --- Item Lookup ---


def lookup_item_by_barcode(barcode: str) -> Optional[dict]:
    """Look up an item in ERPNext by barcode."""
    response = requests.get(
        _api_url("/api/resource/Item"),
        params={
            "filters": f'[["Item Barcode","barcode","=","{barcode}"]]',
            "fields": '["name","item_name","standard_rate","image"]',
            "limit_page_length": 1,
        },
        headers=_get_headers(),
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()

    items = data.get("data", [])
    if not items:
        return None

    item = items[0]
    item_code = item["name"]

    # Get stock quantity from Bin
    stock_qty = get_item_stock_qty(item_code)

    return {
        "item_code": item_code,
        "item_name": item.get("item_name", ""),
        "standard_rate": float(item.get("standard_rate", 0)),
        "stock_qty": stock_qty,
        "barcode": barcode,
        "image": item.get("image", ""),
    }


def get_item_stock_qty(item_code: str, warehouse: str = "") -> float:
    """Get current stock quantity for an item from ERPNext Bin."""
    if not warehouse:
        warehouse = settings.DEFAULT_WAREHOUSE

    response = requests.get(
        _api_url("/api/resource/Bin"),
        params={
            "filters": f'[["item_code","=","{item_code}"],["warehouse","=","{warehouse}"]]',
            "fields": '["actual_qty"]',
            "limit_page_length": 1,
        },
        headers=_get_headers(),
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()

    bins = data.get("data", [])
    if bins:
        return float(bins[0].get("actual_qty", 0))
    return 0.0


# --- Sales Invoice ---


def create_sales_invoice(
    items: list[dict],
    customer: str = "Walk-in Customer",
) -> dict:
    """Create a Sales Invoice in ERPNext."""
    invoice = {
        "doctype": "Sales Invoice",
        "customer": customer,
        "is_pos": 1,
        "items": [
            {
                "item_code": item["item_code"],
                "qty": item["qty"],
                "rate": item["rate"],
            }
            for item in items
        ],
    }

    response = requests.post(
        _api_url("/api/resource/Sales Invoice"),
        json=invoice,
        headers=_get_headers(),
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("data", {})


# --- Dashboard Data ---


def get_all_items(limit: int = 0) -> list[dict]:
    """Fetch all items from ERPNext."""
    params = {
        "fields": '["name","item_name","standard_rate","item_group"]',
        "limit_page_length": limit or 0,
    }
    response = requests.get(
        _api_url("/api/resource/Item"),
        params=params,
        headers=_get_headers(),
        timeout=30,
    )
    response.raise_for_status()
    return response.json().get("data", [])


def get_stock_levels(warehouse: str = "") -> list[dict]:
    """Get stock levels per item from ERPNext Bin."""
    if not warehouse:
        warehouse = settings.DEFAULT_WAREHOUSE

    response = requests.get(
        _api_url("/api/resource/Bin"),
        params={
            "filters": f'[["warehouse","=","{warehouse}"]]',
            "fields": '["item_code","actual_qty","warehouse","valuation_rate"]',
            "limit_page_length": 0,
        },
        headers=_get_headers(),
        timeout=30,
    )
    response.raise_for_status()
    return response.json().get("data", [])


def get_stock_ledger_entries(
    item_code: str = "",
    from_date: str = "",
    to_date: str = "",
    limit: int = 500,
) -> list[dict]:
    """Get stock ledger entries for historical analysis."""
    filters = []
    if item_code:
        filters.append(f'["item_code","=","{item_code}"]')
    if from_date:
        filters.append(f'["posting_date",">=","{from_date}"]')
    if to_date:
        filters.append(f'["posting_date","<=","{to_date}"]')

    response = requests.get(
        _api_url("/api/resource/Stock Ledger Entry"),
        params={
            "filters": f"[{','.join(filters)}]" if filters else "[]",
            "fields": '["item_code","actual_qty","posting_date","voucher_type","warehouse"]',
            "order_by": "posting_date desc",
            "limit_page_length": limit,
        },
        headers=_get_headers(),
        timeout=30,
    )
    response.raise_for_status()
    return response.json().get("data", [])


def get_sales_invoices(
    from_date: str = "",
    to_date: str = "",
    limit: int = 500,
) -> list[dict]:
    """Get sales invoice items for forecasting."""
    filters = []
    if from_date:
        filters.append(f'["posting_date",">=","{from_date}"]')
    if to_date:
        filters.append(f'["posting_date","<=","{to_date}"]')

    response = requests.get(
        _api_url("/api/resource/Sales Invoice"),
        params={
            "filters": f"[{','.join(filters)}]" if filters else "[]",
            "fields": '["name","posting_date","grand_total","customer"]',
            "order_by": "posting_date desc",
            "limit_page_length": limit,
        },
        headers=_get_headers(),
        timeout=30,
    )
    response.raise_for_status()
    return response.json().get("data", [])


def get_sales_data(
    from_date: str = "",
    to_date: str = "",
    limit: int = 200,
) -> list[dict]:
    """Get filtered submitted sales invoices for the sales search feature."""
    filters = ['["docstatus","=","1"]']
    if from_date:
        filters.append(f'["posting_date",">=","{from_date}"]')
    if to_date:
        filters.append(f'["posting_date","<=","{to_date}"]')

    response = requests.get(
        _api_url("/api/resource/Sales Invoice"),
        params={
            "filters": f"[{','.join(filters)}]",
            "fields": '["name","posting_date","customer","grand_total","status"]',
            "order_by": "posting_date desc",
            "limit_page_length": limit,
        },
        headers=_get_headers(),
        timeout=30,
    )
    response.raise_for_status()
    return response.json().get("data", [])


def get_sales_invoice_items(invoice_name: str) -> list[dict]:
    """Get line items from a specific sales invoice."""
    response = requests.get(
        _api_url(f"/api/resource/Sales Invoice/{invoice_name}"),
        params={"fields": '["items"]'},
        headers=_get_headers(),
        timeout=15,
    )
    response.raise_for_status()
    data = response.json().get("data", {})
    return data.get("items", [])
