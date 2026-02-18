import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.udhar import UdharEntry, UdharCreateRequest, UdharUpdateRequest, UdharResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def list_udhar(
    status: str = Query(default="all", description="Pending | Paid | all"),
    customer_name: str = Query(default=""),
    from_date: str = Query(default=""),
    to_date: str = Query(default=""),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List Udhar entries with optional filters."""
    try:
        query = db.query(UdharEntry)
        if status != "all":
            query = query.filter(UdharEntry.status == status)
        if customer_name:
            query = query.filter(
                func.lower(UdharEntry.customer_name).contains(customer_name.lower())
            )
        if from_date:
            query = query.filter(UdharEntry.date_given >= from_date)
        if to_date:
            query = query.filter(UdharEntry.date_given <= to_date)

        total = query.count()
        records = query.order_by(UdharEntry.date_given.desc()).offset(skip).limit(limit).all()
        return {"count": total, "records": [UdharResponse.model_validate(r) for r in records]}
    except Exception as e:
        logger.exception("Failed to list udhar entries")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=UdharResponse, status_code=201)
async def create_udhar(payload: UdharCreateRequest, db: Session = Depends(get_db)):
    """Create a new Udhar entry."""
    try:
        entry = UdharEntry(**payload.model_dump())
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return UdharResponse.model_validate(entry)
    except Exception as e:
        db.rollback()
        logger.exception("Failed to create udhar entry")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{entry_id}", response_model=UdharResponse)
async def update_udhar(
    entry_id: int, payload: UdharUpdateRequest, db: Session = Depends(get_db)
):
    """Update status, due date, or items of an Udhar entry."""
    entry = db.query(UdharEntry).filter(UdharEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Udhar entry not found")
    try:
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(entry, field, value)
        db.commit()
        db.refresh(entry)
        return UdharResponse.model_validate(entry)
    except Exception as e:
        db.rollback()
        logger.exception("Failed to update udhar entry")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{entry_id}")
async def delete_udhar(entry_id: int, db: Session = Depends(get_db)):
    """Delete an Udhar entry."""
    entry = db.query(UdharEntry).filter(UdharEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Udhar entry not found")
    try:
        db.delete(entry)
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        logger.exception("Failed to delete udhar entry")
        raise HTTPException(status_code=500, detail=str(e))
