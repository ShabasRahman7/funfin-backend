from fastapi import APIRouter, Depends, HTTPException, Query, status

from beanie import PydanticObjectId

from app.api.deps import get_admin_or_superadmin, get_super_admin
from app.models.admin import Admin, AdminRole
from app.schemas.admin import (
    AdminActionResponse,
    AdminCreate,
    AdminListResponse,
    AdminSingleResponse,
    AdminUpdate,
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


def _coerce_object_id(raw: str) -> PydanticObjectId:
    try:
        return PydanticObjectId(raw)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid admin id") from exc


@router.post(
    "",
    response_model=AdminActionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create admin (from admin side)",
)
async def create_admin(
    admin_in: AdminCreate,
    current_admin: Admin = Depends(get_admin_or_superadmin),
):
    if (
        admin_in.role == AdminRole.SUPERADMIN
        and current_admin.role != AdminRole.SUPERADMIN
    ):
        raise HTTPException(
            status_code=403, detail="Only superadmin can create another superadmin"
        )

    exists = await Admin.find_one({"email": admin_in.email.lower()})
    if exists:
        raise HTTPException(status_code=409, detail="Admin email already exists")

    new_admin = Admin(
        full_name=admin_in.fullName,
        email=admin_in.email.lower(),
        password=admin_in.password,
        role=admin_in.role,
        is_active=admin_in.isActive,
    )
    await new_admin.insert()

    return {
        "message": "Admin created successfully",
        "admin": _admin_public(new_admin),
    }


@router.get(
    "",
    response_model=AdminListResponse,
    summary="List admins",
)
async def list_admins(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=200),
    current_admin: Admin = Depends(get_admin_or_superadmin),
):
    total = await Admin.find().count()
    admins = (
        await Admin.find()
        .sort(-Admin.created_at)
        .skip(skip)
        .limit(limit)
        .to_list()
    )
    return {"admins": [_admin_public(a) for a in admins], "total": total}


@router.get(
    "/{admin_id}",
    response_model=AdminSingleResponse,
    summary="Get admin by id",
)
async def get_admin(
    admin_id: str,
    current_admin: Admin = Depends(get_admin_or_superadmin),
):
    target = await Admin.get(_coerce_object_id(admin_id))
    if not target:
        raise HTTPException(status_code=404, detail="Admin not found")
    return {"admin": _admin_public(target)}


@router.patch(
    "/{admin_id}",
    response_model=AdminActionResponse,
    summary="Update admin",
)
async def update_admin(
    admin_id: str,
    payload: AdminUpdate,
    current_admin: Admin = Depends(get_admin_or_superadmin),
):
    target = await Admin.get(_coerce_object_id(admin_id))
    if not target:
        raise HTTPException(status_code=404, detail="Admin not found")

    if (
        current_admin.role != AdminRole.SUPERADMIN
        and target.role == AdminRole.SUPERADMIN
    ):
        raise HTTPException(
            status_code=403, detail="Only superadmin can update superadmin"
        )

    if (
        payload.role == AdminRole.SUPERADMIN
        and current_admin.role != AdminRole.SUPERADMIN
    ):
        raise HTTPException(
            status_code=403, detail="Only superadmin can promote to superadmin"
        )

    if payload.email is not None:
        new_email = payload.email.lower()
        if new_email != target.email:
            exists = await Admin.find_one({"email": new_email})
            if exists:
                raise HTTPException(
                    status_code=409, detail="Admin email already exists"
                )
            target.email = new_email

    if payload.fullName is not None:
        target.full_name = payload.fullName
    if payload.password is not None:
        target.password = payload.password
    if payload.role is not None:
        target.role = payload.role
    if payload.isActive is not None:
        target.is_active = payload.isActive

    await target.save()

    return {
        "message": "Admin updated successfully",
        "admin": _admin_public(target),
    }


@router.delete(
    "/{admin_id}",
    summary="Delete admin",
)
async def delete_admin(
    admin_id: str,
    current_admin: Admin = Depends(get_super_admin),
):
    if str(current_admin.id) == admin_id:
        raise HTTPException(
            status_code=400, detail="You cannot delete your own admin account"
        )

    target = await Admin.get(_coerce_object_id(admin_id))
    if not target:
        raise HTTPException(status_code=404, detail="Admin not found")

    await target.delete()
    return {"message": "Admin deleted successfully"}
