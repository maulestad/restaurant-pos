from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class CashSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)

    opened_at: datetime = Field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = None

    opening_amount: float = 0.0
    closing_amount: Optional[float] = None
    expected_amount: Optional[float] = None
    difference: Optional[float] = None

    status: str = Field(default="open")
    notes: str = ""