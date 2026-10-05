from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class Sale(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    total: float = 0.0
    status: str = "pending"
    table_number: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    stock_applied: bool = Field(default=False)
    items: List["SaleItem"] = Relationship(back_populates="sale")

class SaleItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sale_id: int = Field(foreign_key="sale.id")
    product_id: int = Field(foreign_key="product.id")
    product_name: str = ""
    quantity: float = 1
    unit_price: float = 0.0
    subtotal: float = 0.0
    sale: Optional[Sale] = Relationship(back_populates="items")

    stock_before: float = Field(default=0.0)
    stock_after: float = Field(default=0.0)
    stock_applied: bool = Field(default=False)