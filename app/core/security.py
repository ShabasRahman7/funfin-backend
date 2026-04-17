import re
from datetime import datetime, timedelta, timezone
from typing import Any, Literal, Optional, Union

import bcrypt
from jose import jwt

from app.core.config import settings


_BCRYPT_MAX_BYTES = 72


def _prepare_secret(password: str) -> bytes:
    data = password.encode("utf-8")
    if len(data) > _BCRYPT_MAX_BYTES:
        data = data[:_BCRYPT_MAX_BYTES]
    return data


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            _prepare_secret(plain_password),
            hashed_password.encode("utf-8"),
        )
    except ValueError:
        return False


def get_password_hash(password: str) -> str:
    hashed = bcrypt.hashpw(_prepare_secret(password), bcrypt.gensalt(rounds=10))
    return hashed.decode("utf-8")


_DURATION_PATTERN = re.compile(r"^\s*(\d+)\s*([smhd])\s*$", re.IGNORECASE)


def _parse_expires_in(value: Union[str, int, None]) -> timedelta:
    """Parse values like '7d', '24h', '30m', or a raw number of seconds."""
    if value is None:
        return timedelta(minutes=settings.JWT_EXPIRES_IN_MINUTES)

    if isinstance(value, int):
        return timedelta(seconds=value)

    value = str(value).strip()
    if not value:
        return timedelta(minutes=settings.JWT_EXPIRES_IN_MINUTES)

    match = _DURATION_PATTERN.match(value)
    if match:
        qty = int(match.group(1))
        unit = match.group(2).lower()
        if unit == "s":
            return timedelta(seconds=qty)
        if unit == "m":
            return timedelta(minutes=qty)
        if unit == "h":
            return timedelta(hours=qty)
        if unit == "d":
            return timedelta(days=qty)

    if value.isdigit():
        return timedelta(seconds=int(value))

    return timedelta(minutes=settings.JWT_EXPIRES_IN_MINUTES)


def _default_expiry() -> timedelta:
    return _parse_expires_in(settings.JWT_EXPIRES_IN)


def _encode(payload: dict, expires_delta: Optional[timedelta] = None) -> str:
    delta = expires_delta if expires_delta is not None else _default_expiry()
    exp = datetime.now(timezone.utc) + delta
    to_encode = {**payload, "exp": exp}
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm="HS256")


def sign_user_token(
    user_id: Any,
    email: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    payload = {
        "userId": str(user_id),
        "email": email,
        "tokenType": "user",
        "sub": str(user_id),
    }
    return _encode(payload, expires_delta)


def sign_admin_token(
    admin_id: Any,
    email: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    payload = {
        "userId": str(admin_id),
        "email": email,
        "role": role,
        "tokenType": "admin",
        "sub": str(admin_id),
    }
    return _encode(payload, expires_delta)


def create_access_token(
    subject: Union[str, Any],
    role: str = "user",
    expires_delta: Optional[timedelta] = None,
    email: str = "",
    token_type: Literal["user", "admin"] = "user",
) -> str:
    if token_type == "admin":
        return sign_admin_token(subject, email, role, expires_delta)
    return sign_user_token(subject, email, expires_delta)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except jwt.JWTError:
        return None
