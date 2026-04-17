import logging
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.mailer import send_otp_email
from app.core.security import get_password_hash, sign_user_token, verify_password
from app.models.otp import OTP, OtpPurpose
from app.models.user import AuthProvider, User
from app.schemas.auth import (
    AuthLoginResponse,
    ForgotPasswordInput,
    GenericMessageResponse,
    ProfileResponse,
    ResendOtpInput,
    ResetPasswordInput,
    SignupResponse,
    SocialLoginInput,
    UserCreate,
    UserLogin,
    VerifyOtpInput,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _generate_otp() -> str:
    return f"{secrets.randbelow(900000) + 100000:06d}"


def _user_public(user: User) -> dict:
    return {
        "id": str(user.id),
        "fullName": user.full_name,
        "country": user.country,
        "email": user.email,
        "authProvider": (
            user.auth_provider.value
            if getattr(user.auth_provider, "value", None)
            else (user.auth_provider or "local")
        ),
    }


async def _issue_otp(user: User, purpose: OtpPurpose) -> str:
    plain_otp = _generate_otp()
    code_hash = get_password_hash(plain_otp)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXP_MINUTES)

    await OTP.find({"email": user.email, "purpose": purpose}).delete()

    otp_doc = OTP(
        user_id=user.id,
        email=user.email,
        purpose=purpose,
        code_hash=code_hash,
        expires_at=expires_at,
    )
    await otp_doc.insert()
    return plain_otp


async def _verify_and_consume_otp(email: str, otp_code: str, purpose: OtpPurpose) -> None:
    otp_doc = (
        await OTP.find({"email": email, "purpose": purpose})
        .sort(-OTP.created_at)
        .first_or_none()
    )
    if not otp_doc:
        raise HTTPException(
            status_code=400, detail="OTP not found. Please request a new OTP."
        )

    expires_at = otp_doc.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        await OTP.find({"email": email, "purpose": purpose}).delete()
        raise HTTPException(status_code=400, detail="OTP expired")

    if not verify_password(otp_code, otp_doc.code_hash):
        raise HTTPException(status_code=400, detail="Invalid OTP")

    await OTP.find({"email": email, "purpose": purpose}).delete()


@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new user account",
    description="Register a new user with email/password and receive a verification OTP by email.",
)
async def signup_user(user_in: UserCreate):
    normalized_email = user_in.email.lower()
    existing = await User.find_one({"email": normalized_email})

    if existing and existing.auth_provider != AuthProvider.LOCAL:
        raise HTTPException(
            status_code=409,
            detail=(
                f"This email is registered with {existing.auth_provider.value}. "
                "Please use social login."
            ),
        )
    if existing and existing.is_email_verified:
        raise HTTPException(status_code=409, detail="Email already registered")

    if existing:
        user = existing
        user.full_name = user_in.fullName
        user.country = user_in.country
        user.password = user_in.password
        user.auth_provider = AuthProvider.LOCAL
        user.provider_user_id = None
        user.is_email_verified = False
        await user.save()
    else:
        user = User(
            full_name=user_in.fullName,
            country=user_in.country,
            email=normalized_email,
            password=user_in.password,
        )
        await user.insert()

    otp_code = await _issue_otp(user, OtpPurpose.VERIFY_EMAIL)

    try:
        await send_otp_email(
            user.email, user.full_name, otp_code, subject="Verify your email - OTP"
        )
    except Exception as exc:
        logger.exception("Failed to send signup OTP email: %s", exc)

    return {"message": "Signup successful. OTP sent to your email.", "email": user.email}


@router.post(
    "/verify-otp",
    response_model=AuthLoginResponse,
    summary="Verify email OTP",
)
async def verify_otp(payload: VerifyOtpInput):
    normalized_email = payload.email.lower()
    user = await User.find_one({"email": normalized_email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.auth_provider != AuthProvider.LOCAL:
        raise HTTPException(
            status_code=400,
            detail="Social accounts do not require OTP verification",
        )

    await _verify_and_consume_otp(normalized_email, payload.otp, OtpPurpose.VERIFY_EMAIL)

    user.is_email_verified = True
    await user.save()

    token = sign_user_token(user.id, user.email)
    return {
        "message": "Email verified successfully.",
        "token": token,
        "user": _user_public(user),
    }


@router.post(
    "/resend-otp",
    response_model=GenericMessageResponse,
    summary="Resend verification OTP",
)
async def resend_otp(payload: ResendOtpInput):
    normalized_email = payload.email.lower()
    user = await User.find_one({"email": normalized_email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.auth_provider != AuthProvider.LOCAL:
        raise HTTPException(
            status_code=400,
            detail="Social accounts do not support resend OTP",
        )

    otp_code = await _issue_otp(user, OtpPurpose.VERIFY_EMAIL)

    try:
        await send_otp_email(
            user.email, user.full_name, otp_code, subject="Your new OTP code"
        )
    except Exception as exc:
        logger.exception("Failed to resend OTP email: %s", exc)

    return {"message": "New OTP sent successfully."}


@router.post(
    "/login",
    response_model=AuthLoginResponse,
    summary="Login with email and password",
)
async def login(user_in: UserLogin):
    normalized_email = user_in.email.lower()
    user = await User.find_one({"email": normalized_email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if user.auth_provider != AuthProvider.LOCAL:
        raise HTTPException(
            status_code=403,
            detail=(
                f"Use {user.auth_provider.value} login for this account. "
                "Email/password login is disabled."
            ),
        )
    if not user.is_email_verified:
        raise HTTPException(status_code=403, detail="Please verify your email first")
    if not user.check_password(user_in.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = sign_user_token(user.id, user.email)
    return {
        "message": "Login successful",
        "token": token,
        "user": _user_public(user),
    }


@router.post(
    "/social-login",
    response_model=AuthLoginResponse,
    summary="Login or signup with Google/Apple",
)
async def social_login(payload: SocialLoginInput):
    normalized_email = payload.email.lower()
    default_country = payload.country or "Unknown"
    user = await User.find_one({"email": normalized_email})

    if not user:
        synthetic_password = f"{_generate_otp()}{int(datetime.utcnow().timestamp())}{payload.provider}"
        user = User(
            full_name=payload.fullName,
            country=default_country,
            email=normalized_email,
            password=synthetic_password,
            auth_provider=AuthProvider(payload.provider),
            provider_user_id=payload.providerUserId,
            is_email_verified=True,
        )
        await user.insert()
    else:
        if user.auth_provider == AuthProvider.LOCAL:
            raise HTTPException(
                status_code=409,
                detail=(
                    "This email is registered with email/password. Please login using "
                    "email and password."
                ),
            )
        if user.auth_provider.value != payload.provider:
            raise HTTPException(
                status_code=403,
                detail=(
                    f"This account is linked with {user.auth_provider.value}. "
                    f"Please continue with {user.auth_provider.value}."
                ),
            )
        if user.provider_user_id and user.provider_user_id != payload.providerUserId:
            raise HTTPException(
                status_code=403, detail="Invalid social account identifier"
            )

        user.full_name = payload.fullName
        user.country = payload.country or user.country
        user.provider_user_id = payload.providerUserId
        user.is_email_verified = True
        await user.save()

    token = sign_user_token(user.id, user.email)
    return {
        "message": f"{payload.provider} login successful",
        "token": token,
        "user": _user_public(user),
    }


@router.post(
    "/forgot-password",
    response_model=GenericMessageResponse,
    summary="Send password reset OTP",
)
async def forgot_password(payload: ForgotPasswordInput):
    normalized_email = payload.email.lower()
    user = await User.find_one({"email": normalized_email})

    generic = {"message": "If the email exists, an OTP has been sent."}
    if not user:
        return generic

    if user.auth_provider != AuthProvider.LOCAL:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Password reset is unavailable for {user.auth_provider.value} "
                "accounts. Use social login."
            ),
        )

    otp_code = await _issue_otp(user, OtpPurpose.RESET_PASSWORD)

    try:
        await send_otp_email(
            user.email, user.full_name, otp_code, subject="Reset your password - OTP"
        )
    except Exception as exc:
        logger.exception("Failed to send reset OTP email: %s", exc)

    return generic


@router.post(
    "/reset-password",
    response_model=GenericMessageResponse,
    summary="Reset password using email + OTP",
)
async def reset_password(payload: ResetPasswordInput):
    normalized_email = payload.email.lower()
    user = await User.find_one({"email": normalized_email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.auth_provider != AuthProvider.LOCAL:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Password reset is unavailable for {user.auth_provider.value} "
                "accounts. Use social login."
            ),
        )

    await _verify_and_consume_otp(normalized_email, payload.otp, OtpPurpose.RESET_PASSWORD)

    user.password = payload.newPassword
    await user.save()

    return {"message": "Password reset successful"}


@router.get(
    "/profile",
    response_model=ProfileResponse,
    summary="Get current user profile",
)
async def read_current_user(current_user: User = Depends(get_current_user)):
    return {
        "user": {
            "id": str(current_user.id),
            "fullName": current_user.full_name,
            "country": current_user.country,
            "email": current_user.email,
            "authProvider": (
                current_user.auth_provider.value
                if getattr(current_user.auth_provider, "value", None)
                else "local"
            ),
            "isEmailVerified": current_user.is_email_verified,
        }
    }
