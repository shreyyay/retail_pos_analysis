import os
import logging
import uuid

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.config import settings
from app.models.invoice import InvoiceUploadResponse, InvoiceData, StockInConfirmRequest
from app.models.stock_entry import StockEntryResponse
from app.services import ocr_service, extraction_service, erpnext_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload", response_model=InvoiceUploadResponse)
async def upload_invoice(file: UploadFile = File(...)):
    """Upload a supplier invoice (image or PDF) for OCR + AI extraction."""
    allowed_types = {
        "image/jpeg", "image/png", "image/webp",
        "application/pdf",
    }
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Use JPEG, PNG, WebP, or PDF.",
        )

    # Save uploaded file
    ext = os.path.splitext(file.filename or "invoice")[1] or ".jpg"
    filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    try:
        # Step 1: OCR
        raw_text = ocr_service.extract_text(file_path)
        if not raw_text.strip():
            return InvoiceUploadResponse(
                success=False,
                message="Could not extract text from the uploaded file. Please try a clearer image.",
            )

        # Step 2: AI Extraction
        invoice_data = extraction_service.extract_invoice_data(raw_text)

        return InvoiceUploadResponse(
            success=True,
            message=f"Extracted {len(invoice_data.line_items)} line items from invoice",
            data=invoice_data,
        )

    except Exception as e:
        logger.exception("Invoice processing failed")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    finally:
        # Clean up uploaded file
        if os.path.exists(file_path):
            os.remove(file_path)


@router.post("/confirm", response_model=StockEntryResponse)
async def confirm_stock_in(request: StockInConfirmRequest):
    """Confirm extracted invoice data and create a Stock Entry (Material Receipt) in ERPNext."""
    if not request.line_items:
        raise HTTPException(status_code=400, detail="No line items to process")

    items = [
        {
            "item_code": item.item_name,
            "qty": item.quantity,
            "basic_rate": item.unit_price,
        }
        for item in request.line_items
    ]

    try:
        result = erpnext_service.create_stock_entry(
            items=items,
            supplier=request.header.supplier_name,
            invoice_no=request.header.invoice_number,
            entry_type="Material Receipt",
            warehouse=request.warehouse,
        )
        return StockEntryResponse(**result)

    except Exception as e:
        logger.exception("Stock entry creation failed")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create stock entry: {str(e)}",
        )
