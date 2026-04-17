from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    fullName: str = Field(min_length=2)
    country: str = Field(min_length=2)
    email: EmailStr
    password: str = Field(min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class SocialLoginInput(BaseModel):
    provider: Literal["google", "apple", "facebook", "microsoft"]
    providerUserId: str = Field(min_length=2)
    email: EmailStr
    fullName: str = Field(min_length=2)
    country: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    fullName: str
    email: EmailStr
    country: str
    authProvider: Optional[str] = None
    isEmailVerified: Optional[bool] = None


class AuthLoginResponse(BaseModel):
    message: str
    token: str
    user: UserResponse


class ProfileResponse(BaseModel):
    user: UserResponse


class SignupResponse(BaseModel):
    message: str
    email: EmailStr


class GenericMessageResponse(BaseModel):
    message: str


class VerifyOtpInput(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


OtpVerify = VerifyOtpInput


class ResendOtpInput(BaseModel):
    email: EmailStr


class ForgotPasswordInput(BaseModel):
    email: EmailStr


class ResetPasswordInput(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
    newPassword: str = Field(min_length=6)
