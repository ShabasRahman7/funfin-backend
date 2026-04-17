from __future__ import annotations

import asyncio

from app.core.config import settings
from app.core.db import init_db
from app.models.admin import Admin, AdminRole


def _normalize_role(role: str) -> AdminRole:
    allowed = {r.value for r in AdminRole}
    if role not in allowed:
        raise RuntimeError(
            f"Invalid DEFAULT_ADMIN_ROLE: {role}. Allowed: {', '.join(sorted(allowed))}"
        )
    return AdminRole(role)


async def run() -> None:
    await init_db()

    email = str(settings.DEFAULT_ADMIN_EMAIL).lower()
    password = settings.DEFAULT_ADMIN_PASSWORD
    full_name = settings.DEFAULT_ADMIN_FULLNAME
    role = _normalize_role(settings.DEFAULT_ADMIN_ROLE)

    existing = await Admin.find_one(Admin.email == email)

    if existing is None:
        admin = Admin(
            full_name=full_name,
            email=email,
            password=password,
            role=role,
            is_active=True,
        )
        await admin.insert()
        print(f"Created default admin: {admin.email} ({admin.role.value})")
    else:
        existing.full_name = full_name
        existing.password = password
        existing.role = role
        existing.is_active = True
        await existing.save()
        print(f"Updated default admin: {existing.email} ({existing.role.value})")


def main() -> None:
    try:
        asyncio.run(run())
    except Exception as exc:
        print(f"Default admin seed failed: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
