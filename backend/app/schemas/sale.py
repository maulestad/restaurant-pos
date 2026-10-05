from typing import List, Optional
from pydantic import BaseModel

class SaleItemIn(BaseModel):
    product_id: int
    quantity: float = 1

class SaleCreate(BaseModel):
    items: List[SaleItemIn]
    table_number: Optional[int] = None

class SaleItemOut(BaseModel):
    product_id: int
    product_name: str
    quantity: float
    unit_price: float
    subtotal: float

class SaleOut(BaseModel):
    id: int
    user_id: int
    total: float
    status: str
    table_number: Optional[int]
    created_at: str
    items: List[SaleItemOut] = []