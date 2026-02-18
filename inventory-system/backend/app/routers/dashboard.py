import logging

from fastapi import APIRouter, HTTPException, Query

from app.services import analytics_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/summary")
async def dashboard_summary():
    """Get overall inventory dashboard summary."""
    try:
        return analytics_service.get_dashboard_summary()
    except Exception as e:
        logger.exception("Failed to fetch dashboard summary")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reorder-alerts")
async def reorder_alerts():
    """Get items that need reordering."""
    try:
        alerts = analytics_service.get_reorder_alerts()
        return {"count": len(alerts), "alerts": alerts}
    except Exception as e:
        logger.exception("Failed to fetch reorder alerts")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dead-stock")
async def dead_stock(days: int = Query(default=90, ge=1, le=365)):
    """Get items with no stock movement in the specified number of days."""
    try:
        items = analytics_service.get_dead_stock(days=days)
        return {"count": len(items), "days_threshold": days, "items": items}
    except Exception as e:
        logger.exception("Failed to fetch dead stock")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/demand-forecast/{item_code}")
async def demand_forecast(item_code: str, periods: int = Query(default=4, ge=1, le=12)):
    """Get demand forecast for a specific item."""
    try:
        return analytics_service.get_demand_forecast(item_code=item_code, periods=periods)
    except Exception as e:
        logger.exception("Failed to generate demand forecast")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sales-velocity")
async def sales_velocity(days: int = Query(default=30, ge=1, le=365)):
    """Get sales velocity for all items over the specified period."""
    try:
        velocity = analytics_service.get_sales_velocity(days=days)
        return {"period_days": days, "items": velocity}
    except Exception as e:
        logger.exception("Failed to fetch sales velocity")
        raise HTTPException(status_code=500, detail=str(e))
