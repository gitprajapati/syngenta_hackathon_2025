#schemas/user.py
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    employee_id: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    employee_id: str
    role_name: str
    scope: str
    region_name: str
    department_name: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    email: str
    employee_id: Optional[str]
    is_active: bool
    scope: Optional[str]
    role: Optional[str]
    department: Optional[str] 
    region: Optional[str] 
    last_login: Optional[datetime]
    created_at: datetime

    class Config:
        orm_mode = True