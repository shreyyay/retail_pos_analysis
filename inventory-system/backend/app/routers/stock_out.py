import logging

from fastapi import APIRouter, HTTPException

from app.models.stock_entry import (
    ItemLookupResponse,
    SaleRequest,
    SaleResponse,
)
from app.services import erpnext_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/lookup/{barcode}", response_model=ItemLookupResponse)
async def lookup_item(barcode: str):
    """Look up an item by barcode from ERPNext."""
    item = erpnext_service.lookup_item_by_barcode(barcode)
    if not item:
        return ItemLookupResponse(
            success=False,
            message=f"No item found for barcode: {barcode}",
        )

    return ItemLookupResponse(success=True, **item)


@router.post("/sale", response_model=SaleResponse)
async def process_sale(request: SaleRequest):
    """Process a sale: create Material Issue stock entry and optionally a Sales Invoice."""
    if not request.items:
        raise HTTPException(status_code=400, detail="No items in the sale")

    # Create stock deduction (Material Issue)
    stock_items = [
        {
            "item_code": item.item_code,
            "qty": item.qty,
            "basic_rate": item.rate,
        }
        for item in request.items
    ]

    try:
        result = erpnext_service.create_stock_entry(
            items=stock_items,
            supplier="",
            invoice_no="",
            entry_type="Material Issue",
            warehouse=request.warehouse,
        )

        invoice_name = None
        if request.create_invoice:
            invoice_items = [
                {
                    "item_code": item.item_code,
                    "qty": item.qty,
                    "rate": item.rate,
                }
                for item in request.items
            ]
            invoice = erpnext_service.create_sales_invoice(
                items=invoice_items,
                customer=request.customer or "Walk-in Customer",
            )
            invoice_name = invoice.get("name")

        return SaleResponse(
            success=True,
            message="Sale processed successfully",
            stock_entry_name=result.get("entry_name", ""),
            invoice_name=invoice_name,
        )

    except Exception as e:
        logger.exception("Sale processing failed")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process sale: {str(e)}",
        )
