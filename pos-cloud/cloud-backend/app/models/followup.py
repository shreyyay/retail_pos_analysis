from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, Date, DateTime, Integer, String, Text

from app.database import Base


class FollowupEntry(Base):
    __tablename__ = "followup"
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(String(64), nullable=False, index=True)
    customer_name = Column(String(255), nullable=False, index=True)
    phone = Column(String(32), nullable=False)
    salesperson = Column(String(255), nullable=False, index=True)
    notes = Column(Text, nullable=False)
    followup_date = Column(Date, nullable=False)
    next_followup_date = Column(Date, nullable=True)
    status = Column(String(32), nullable=False, default="Open")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FollowupCreateRequest(BaseModel):
    customer_name: str
    phone: str
    salesperson: str
    notes: str
    followup_date: date
    next_followup_date: Optional[date] = None
    status: str = "Open"


class FollowupUpdateRequest(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    next_followup_date: Optional[date] = None


class FollowupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    store_id: str
    customer_name: str
    phone: str
    salesperson: str
    notes: str
    followup_date: date
    next_followup_date: Optional[date]
    status: str
    created_at: datetime
    updated_at: datetime
