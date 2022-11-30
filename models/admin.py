from pydantic import BaseModel
from typing import Optional


class adminUpdate(BaseModel):
    name: str
    last_name: str
    phone: Optional[str]


class registerAdmin(BaseModel):
    name: str
    last_name: str
    email: str
    phone: Optional[str]
    password: str
    suspended: bool
