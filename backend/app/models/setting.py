from typing import Optional
from sqlmodel import SQLModel, Field

class Setting(SQLModel, table=True):
    """Configuraciones clave/valor editables por sysadmin."""
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(unique=True, index=True)
    value: str = ""
    description: str = ""