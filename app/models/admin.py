from datetime import datetime
from enum import Enum

import pymongo
from pydantic import ConfigDict, EmailStr, Field

from beanie import Document, Insert, Replace, Save, SaveChanges, Update, before_event

from app.core.security import get_password_hash, verify_password


class AdminRole(str, Enum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    MENTOR = "mentor"
    COUNSILOR = "counsilor"


class Admin(Document):
    full_name: str = Field(alias="fullName")
    email: EmailStr
    password: str
    role: AdminRole = AdminRole.ADMIN
    is_active: bool = Field(default=True, alias="isActive")

    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True)

    class Settings:
        name = "admins"
        use_state_management = True
        indexes = [
            pymongo.IndexModel(
                [("email", pymongo.ASCENDING)],
                name="email_1",
                unique=True,
                background=True,
            ),
        ]

    @before_event(Insert)
    async def _hash_on_insert(self) -> None:
        if self.password and not self.password.startswith("$2"):
            self.password = get_password_hash(self.password)
        self.updated_at = datetime.utcnow()

    @before_event(Replace, Save, SaveChanges, Update)
    async def _hash_on_update(self) -> None:
        if self.password and not self.password.startswith("$2"):
            self.password = get_password_hash(self.password)
        self.updated_at = datetime.utcnow()

    def check_password(self, password: str) -> bool:
        return verify_password(password, self.password)
