from pydantic import BaseModel
from typing import Optional
import json


class loginModel(BaseModel):
    email: str
    password: str


class passwordChange(BaseModel):
    password: str
    newPassword: str


class passwordRestore(BaseModel):
    password: str
