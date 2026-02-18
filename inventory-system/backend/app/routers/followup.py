import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.followup import (
    FollowupEntry,
    FollowupCreateRequest,
    FollowupUpdateRequest,
    FollowupResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def list_followups(
    status: str = Query(default="all", description="Open | Closed | all"),
    customer_name: str = Query(default=""),
    salesperson: str = Query(default=""),
    from_date: str = Query(default=""),
    to_date: str = Query(default=""),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List Follow-up entries with optional filters."""
    try:
        query = db.query(FollowupEntry)
        if status != "all":
            query = query.filter(FollowupEntry.status == status)
        if customer_name:
            query = query.filter(
                func.lower(FollowupEntry.customer_name).contains(customer_name.lower())
            )
        if salesperson:
            query = query.filter(
                func.lower(FollowupEntry.salesperson).contains(salesperson.lower())
            )
        if from_date:
            query = query.filter(FollowupEntry.followup_date >= from_date)
        if to_date:
            query = query.filter(FollowupEntry.followup_date <= to_date)

        total = query.count()
        records = (
            query.order_by(FollowupEntry.followup_date.desc()).offset(skip).limit(limit).all()
        )
        return {"count": total, "records": [FollowupResponse.model_validate(r) for r in records]}
    except Exception as e:
        logger.exception("Failed to list follow-up entries")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=FollowupResponse, status_code=201)
async def create_followup(payload: FollowupCreateRequest, db: Session = Depends(get_db)):
    """Create a new Follow-up entry."""
    try:
        entry = FollowupEntry(**payload.model_dump())
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return FollowupResponse.model_validate(entry)
    except Exception as e:
        db.rollback()
        logger.exception("Failed to create follow-up entry")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{entry_id}", response_model=FollowupResponse)
async def update_followup(
    entry_id: int, payload: FollowupUpdateRequest, db: Session = Depends(get_db)
):
    """Update status, notes, or next follow-up date."""
    entry = db.query(FollowupEntry).filter(FollowupEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Follow-up entry not found")
    try:
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(entry, field, value)
        db.commit()
        db.refresh(entry)
        return FollowupResponse.model_validate(entry)
    except Exception as e:
        db.rollback()
        logger.exception("Failed to update follow-up entry")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{entry_id}")
async def delete_followup(entry_id: int, db: Session = Depends(get_db)):
    """Delete a Follow-up entry."""
    entry = db.query(FollowupEntry).filter(FollowupEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Follow-up entry not found")
    try:
        db.delete(entry)
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        logger.exception("Failed to delete follow-up entry")
        raise HTTPException(status_code=500, detail=str(e))
