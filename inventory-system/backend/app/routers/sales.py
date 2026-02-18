import logging

import requests as http_requests
from fastapi import APIRouter, HTTPException, Query

from app.services import sales_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/search")
async def search_sales(
    period: str = Query(default="7d", description="today | 7d | 30d | custom"),
    from_date: str = Query(default="", description="YYYY-MM-DD, required when period=custom"),
    to_date: str = Query(default="", description="YYYY-MM-DD, required when period=custom"),
    limit: int = Query(default=200, ge=1, le=1000),
):
    """Search sales invoices filtered by date period."""
    if period == "custom" and (not from_date or not to_date):
        raise HTTPException(
            status_code=400,
            detail="from_date and to_date are required when period=custom",
        )
    try:
        return sales_service.search_sales(
            period=period,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
        )
    except http_requests.ConnectionError:
        raise HTTPException(status_code=503, detail="ERPNext is offline or unreachable")
    except http_requests.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"ERPNext error: {e}")
    except Exception as e:
        logger.exception("Failed to search sales")
        raise HTTPException(status_code=500, detail=str(e))
