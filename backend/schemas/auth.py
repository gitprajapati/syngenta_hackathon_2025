# schemas/auth.py
from pydantic import BaseModel
from typing import Union, Dict, Any, Optional

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str 

class UserCreate(BaseModel):
    email: str
    password: str
    employee_id: str
    role_name: str
    scope: str
    region_name: str
    department_name: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    employee_id: Optional[str]
    is_active: bool
    scope: Optional[str]
    role: Optional[str]
    department: Optional[str]
    region: Optional[str]

    class Config:
        orm_mode = True