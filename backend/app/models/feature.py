from typing import Optional
from sqlmodel import SQLModel, Field

class Feature(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    enabled: bool = Field(default=False)
    description: str = ""