from typing import List, Optional

from pydantic import EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Settings
    PORT: int = 5001
    CLIENT_PORT: int = 5001
    ADMIN_PORT: int = 5002
    NODE_ENV: str = "development"
    ENVIRONMENT: str = "development"
    APP_BASE_URL: str = "http://localhost:5001"
    CLIENT_BASE_URL: str = "http://localhost:5001"
    ADMIN_BASE_URL: str = "http://localhost:5002"

    # MongoDB Config
    MONGODB_URI: str = "mongodb://127.0.0.1:27017/lms-backend"

    # JWT Auth Config
    JWT_SECRET: str = "your_super_secret_jwt_key"
    JWT_EXPIRES_IN: str = "7d"
    JWT_EXPIRES_IN_MINUTES: int = 10080

    # Email Config
    MAIL_HOST: str = "smtp.gmail.com"
    MAIL_PORT: int = 587
    MAIL_USER: str = ""
    MAIL_PASS: str = ""
    MAIL_FROM: str = "CLT Academy <noreply@clt-academy.com>"
    OTP_EXP_MINUTES: int = 10

    # Default Admin Seed Config
    DEFAULT_ADMIN_FULLNAME: str = "Super Admin"
    DEFAULT_ADMIN_EMAIL: EmailStr = "admin@example.com"
    DEFAULT_ADMIN_PASSWORD: str = "ChangeMe123!"
    DEFAULT_ADMIN_ROLE: str = "superadmin"

    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # Cloudflare R2 Uploads Config
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = "lms-media"
    R2_PUBLIC_URL: str = "https://your_public_domain.com"

    # CORS / Allowed origins
    FRONTEND_URL: Optional[str] = None
    ADMIN_URL: Optional[str] = None

    _DEFAULT_ALLOWED_ORIGINS: List[str] = [
        "https://admin-funfin.vercel.app",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5001",
        "http://localhost:5002",
        "https://course.clt-academy.com",
        "https://api-fun-fin.clt-academy.com",
        "https://api-admin-fun-fin.clt-academy.com",
        "http://course1.clt-academy.com",
        "https://main.clt-academy.com",
        "http://localhost:8080",
        "https://fun-fin-theta.vercel.app",
    ]

    @property
    def allowed_origins(self) -> List[str]:
        dynamic = [self.FRONTEND_URL, self.ADMIN_URL]
        return [o for o in [*dynamic, *self._DEFAULT_ALLOWED_ORIGINS] if o]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
