from typing import Optional
from sqlmodel import SQLModel, Field

class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    price: float = 0.0
    category: str = "general"
    active: bool = Field(default=True)

    # Inventario latente (no restrictivo si el flag está apagado)
    track_stock: bool = Field(default=False)
    stock: float = Field(default=0.0)
    min_stock: float = Field(default=0.0)
    unit: str = Field(default="unidad")