from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.admin import AdminRole


class AdminCreate(BaseModel):
    fullName: str = Field(min_length=2)
    email: EmailStr
    password: str = Field(min_length=6)
    role: AdminRole = AdminRole.ADMIN
    isActive: bool = True


class AdminBootstrap(BaseModel):
    fullName: str = Field(min_length=2)
    email: EmailStr
    password: str = Field(min_length=6)
    isActive: bool = True


class AdminLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class AdminUpdate(BaseModel):
    fullName: Optional[str] = Field(default=None, min_length=2)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(default=None, min_length=6)
    role: Optional[AdminRole] = None
    isActive: Optional[bool] = None


class AdminResponse(BaseModel):
    id: str
    fullName: str
    email: EmailStr
    role: AdminRole
    isActive: bool


class AdminLoginResponse(BaseModel):
    message: str
    token: str
    admin: AdminResponse


class AdminProfileResponse(BaseModel):
    admin: AdminResponse


class AdminActionResponse(BaseModel):
    message: str
    admin: AdminResponse


class AdminSingleResponse(BaseModel):
    admin: AdminResponse


class AdminListResponse(BaseModel):
    admins: List[AdminResponse]
    total: int
