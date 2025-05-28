#schemas/role.py
from pydantic import BaseModel
from datetime import datetime
from typing import List

class PermissionBase(BaseModel):
    resource_type: str
    actions: List[str]
    scope: str

class RoleCreate(BaseModel):
    name: str
    description: str
    permissions: List[PermissionBase]

class RoleResponse(RoleCreate):
    id: int
    is_system_role: bool
    created_at: datetime

    class Config:
        from_attributes = True