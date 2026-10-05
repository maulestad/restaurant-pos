from typing import Optional
from sqlmodel import SQLModel, Field


class Branding(SQLModel, table=True):
    """Configuración visual del sistema (una sola fila, id=1)."""
    id: Optional[int] = Field(default=None, primary_key=True)
    system_name: str = Field(default="Restaurant POS")
    logo_base64: str = Field(default="")
    primary_color: str = Field(default="#2563eb")
    updated_at: str = Field(default="")