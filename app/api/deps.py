from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from beanie import PydanticObjectId

from app.core.security import decode_access_token
from app.models.admin import Admin, AdminRole
from app.models.user import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
admin_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/admin-auth/login", auto_error=False
)


def _extract_bearer_token(request: Request) -> Optional[str]:
    auth = request.headers.get("authorization")
    if not auth:
        return None
    parts = auth.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1]


def _decode_or_401(token: Optional[str], detail: str) -> dict:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token missing or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def _payload_user_id(payload: dict) -> Optional[str]:
    return payload.get("userId") or payload.get("sub")


async def get_current_user(request: Request) -> User:
    token = _extract_bearer_token(request)
    payload = _decode_or_401(token, "Invalid or expired token")

    token_type = payload.get("tokenType")
    if token_type is not None and token_type != "user":
        raise HTTPException(status_code=401, detail="Invalid token type for user")

    user_id = _payload_user_id(payload)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    try:
        user = await User.get(PydanticObjectId(user_id))
    except Exception:
        user = None
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    return user


async def get_current_admin(request: Request) -> Admin:
    token = _extract_bearer_token(request)
    payload = _decode_or_401(token, "Invalid or expired token")

    token_type = payload.get("tokenType")
    if token_type is not None and token_type != "admin":
        raise HTTPException(status_code=401, detail="Invalid token type for admin")

    admin_id = _payload_user_id(payload)
    if not admin_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    try:
        admin = await Admin.get(PydanticObjectId(admin_id))
    except Exception:
        admin = None
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid token")
    if not admin.is_active:
        raise HTTPException(status_code=403, detail="Admin account is inactive")

    return admin


def require_roles(*allowed_roles: AdminRole):
    allowed = set(r.value if isinstance(r, AdminRole) else r for r in allowed_roles)

    async def _dep(current_admin: Admin = Depends(get_current_admin)) -> Admin:
        if current_admin.role.value not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: insufficient role",
            )
        return current_admin

    return _dep


get_super_admin = require_roles(AdminRole.SUPERADMIN)
get_admin_or_superadmin = require_roles(AdminRole.SUPERADMIN, AdminRole.ADMIN)
get_editor_admin = require_roles(
    AdminRole.SUPERADMIN, AdminRole.ADMIN, AdminRole.MENTOR
)
