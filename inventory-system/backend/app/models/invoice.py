from typing import Optional

from pydantic import BaseModel


class InvoiceHeader(BaseModel):
    supplier_name: str = ""
    invoice_number: str = ""
    invoice_date: str = ""


class LineItem(BaseModel):
    item_name: str
    quantity: float
    unit: str = "pcs"
    unit_price: float
    total: float
    gst_rate: str = ""


class TaxSummary(BaseModel):
    cgst_amount: float = 0.0
    sgst_amount: float = 0.0
    igst_amount: float = 0.0
    total_tax: float = 0.0


class PaymentInfo(BaseModel):
    payment_terms: str = ""
    due_date: str = ""
    bank_details: str = ""


class InvoiceData(BaseModel):
    header: InvoiceHeader = InvoiceHeader()
    line_items: list[LineItem] = []
    tax_summary: TaxSummary = TaxSummary()
    payment_info: PaymentInfo = PaymentInfo()
    raw_text: str = ""


class InvoiceUploadResponse(BaseModel):
    success: bool
    message: str
    data: Optional[InvoiceData] = None


class StockInConfirmRequest(BaseModel):
    header: InvoiceHeader
    line_items: list[LineItem]
    warehouse: str = "Stores - Company"
