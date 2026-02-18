from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, Date, DateTime, Integer, Numeric, String, Text, func

from app.database import Base


# --- SQLAlchemy ORM table ---

class UdharEntry(Base):
    __tablename__ = "udhar"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, nullable=False, index=True)
    phone = Column(String, nullable=False)
    items = Column(Text, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    date_given = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(String, nullable=False, default="Pending")  # Pending | Paid
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# --- Pydantic schemas ---

class UdharCreateRequest(BaseModel):
    customer_name: str
    phone: str
    items: str
    amount: float
    date_given: date
    due_date: date
    status: str = "Pending"


class UdharUpdateRequest(BaseModel):
    status: Optional[str] = None
    due_date: Optional[date] = None
    items: Optional[str] = None
    amount: Optional[float] = None


class UdharResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_name: str
    phone: str
    items: str
    amount: float
    date_given: date
    due_date: date
    status: str
    created_at: datetime
    updated_at: datetime
