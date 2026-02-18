from typing import Optional

from pydantic import BaseModel


class StockEntryItem(BaseModel):
    item_code: str
    qty: float
    basic_rate: float
    t_warehouse: str = ""
    s_warehouse: str = ""


class StockEntry(BaseModel):
    doctype: str = "Stock Entry"
    stock_entry_type: str = "Material Receipt"
    supplier: str = ""
    items: list[StockEntryItem] = []


class StockEntryResponse(BaseModel):
    success: bool
    message: str
    entry_name: str = ""
    entry_url: str = ""


class ItemLookupResponse(BaseModel):
    success: bool
    item_code: str = ""
    item_name: str = ""
    standard_rate: float = 0.0
    stock_qty: float = 0.0
    barcode: str = ""
    image: str = ""


class SaleItem(BaseModel):
    item_code: str
    item_name: str
    qty: float
    rate: float


class SaleRequest(BaseModel):
    items: list[SaleItem]
    warehouse: str = "Stores - Company"
    customer: str = ""
    create_invoice: bool = False


class SaleResponse(BaseModel):
    success: bool
    message: str
    stock_entry_name: str = ""
    invoice_name: Optional[str] = None
