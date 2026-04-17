from datetime import datetime
from enum import Enum

from pydantic import ConfigDict, EmailStr, Field

from beanie import Document, PydanticObjectId


class OtpPurpose(str, Enum):
    VERIFY_EMAIL = "VERIFY_EMAIL"
    RESET_PASSWORD = "RESET_PASSWORD"


class OTP(Document):
    user_id: PydanticObjectId = Field(alias="user")
    email: EmailStr
    purpose: OtpPurpose
    code_hash: str = Field(alias="codeHash")
    expires_at: datetime = Field(alias="expiresAt")

    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True)

    class Settings:
        name = "otps"
        indexes = [
            "user",
            "email",
            "purpose",
            [("email", 1), ("purpose", 1)],
        ]
