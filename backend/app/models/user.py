from typing import Optional
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    full_name: str = ""
    password_hash: str
    role: str = Field(default="vendedor")
    active: bool = Field(default=True)