import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.followup import FollowupEntry, FollowupCreateRequest, FollowupUpdateRequest, FollowupResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def list_followups(
    store_id: str = Query(...),
    status: str = Query(default="all"),
    customer_name: str = Query(default=""),
    salesperson: str = Query(default=""),
    from_date: str = Query(default=""),
    to_date: str = Query(default=""),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    try:
        q = db.query(FollowupEntry).filter(FollowupEntry.store_id == store_id)
        if status != "all":
            q = q.filter(FollowupEntry.status == status)
        if customer_name:
            q = q.filter(func.lower(FollowupEntry.customer_name).contains(customer_name.lower()))
        if salesperson:
            q = q.filter(func.lower(FollowupEntry.salesperson).contains(salesperson.lower()))
        if from_date:
            q = q.filter(FollowupEntry.followup_date >= from_date)
        if to_date:
            q = q.filter(FollowupEntry.followup_date <= to_date)
        total = q.count()
        records = q.order_by(FollowupEntry.followup_date.desc()).offset(skip).limit(limit).all()
        return {"count": total, "records": [FollowupResponse.model_validate(r) for r in records]}
    except Exception as e:
        logger.exception("list_followups failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=FollowupResponse, status_code=201)
async def create_followup(
    store_id: str = Query(...),
    payload: FollowupCreateRequest = ...,
    db: Session = Depends(get_db),
):
    try:
        entry = FollowupEntry(store_id=store_id, **payload.model_dump())
        db.add(entry); db.commit(); db.refresh(entry)
        return FollowupResponse.model_validate(entry)
    except Exception as e:
        db.rollback(); raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{entry_id}", response_model=FollowupResponse)
async def update_followup(
    entry_id: int,
    store_id: str = Query(...),
    payload: FollowupUpdateRequest = ...,
    db: Session = Depends(get_db),
):
    entry = db.query(FollowupEntry).filter(FollowupEntry.id == entry_id, FollowupEntry.store_id == store_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Not found")
    try:
        for f, v in payload.model_dump(exclude_none=True).items():
            setattr(entry, f, v)
        db.commit(); db.refresh(entry)
        return FollowupResponse.model_validate(entry)
    except Exception as e:
        db.rollback(); raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{entry_id}")
async def delete_followup(entry_id: int, store_id: str = Query(...), db: Session = Depends(get_db)):
    entry = db.query(FollowupEntry).filter(FollowupEntry.id == entry_id, FollowupEntry.store_id == store_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Not found")
    try:
        db.delete(entry); db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback(); raise HTTPException(status_code=500, detail=str(e))
