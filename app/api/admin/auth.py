from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_admin
from app.core.security import sign_admin_token
from app.models.admin import Admin, AdminRole
from app.schemas.admin import (
    AdminActionResponse,
    AdminBootstrap,
    AdminLogin,
    AdminLoginResponse,
    AdminProfileResponse,
)

router = APIRouter()


def _admin_public(admin: Admin) -> dict:
    return {
        "id": str(admin.id),
        "fullName": admin.full_name,
        "email": admin.email,
        "role": admin.role,
        "isActive": admin.is_active,
    }


@router.post(
    "/bootstrap-superadmin",
    response_model=AdminActionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bootstrap first superadmin",
)
async def bootstrap_superadmin(admin_in: AdminBootstrap):
    count = await Admin.find().count()
    if count > 0:
        raise HTTPException(
            status_code=403, detail="Bootstrap disabled. Admin already exists."
        )

    superadmin = Admin(
        full_name=admin_in.fullName,
        email=admin_in.email.lower(),
        password=admin_in.password,
        role=AdminRole.SUPERADMIN,
        is_active=admin_in.isActive,
    )
    await superadmin.insert()

    return {
        "message": "Superadmin created successfully",
        "admin": _admin_public(superadmin),
    }


@router.post(
    "/login",
    response_model=AdminLoginResponse,
    summary="Login admin",
)
async def login(admin_in: AdminLogin):
    admin = await Admin.find_one({"email": admin_in.email.lower()})
    if not admin or not admin.check_password(admin_in.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not admin.is_active:
        raise HTTPException(status_code=403, detail="Admin account is inactive")

    token = sign_admin_token(admin.id, admin.email, admin.role.value)
    return {
        "message": "Admin login successful",
        "token": token,
        "admin": _admin_public(admin),
    }


@router.get(
    "/profile",
    response_model=AdminProfileResponse,
    summary="Get current admin profile",
)
async def read_current_admin(current_admin: Admin = Depends(get_current_admin)):
    return {"admin": _admin_public(current_admin)}
