import mimetypes
import uuid

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings


def _is_r2_configured() -> bool:
    return bool(
        settings.R2_ACCOUNT_ID
        and settings.R2_ACCESS_KEY_ID
        and settings.R2_SECRET_ACCESS_KEY
    )


def get_r2_client():
    if not _is_r2_configured():
        return None

    return boto3.client(
        "s3",
        endpoint_url=f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name="auto",
    )


def _require_client():
    client = get_r2_client()
    if client is None:
        if settings.ENVIRONMENT == "development":
            return None
        raise RuntimeError("R2 storage is not configured")
    return client


def upload_to_r2(file_content: bytes, original_filename: str, folder: str) -> dict:
    """Upload a byte array to Cloudflare R2 and return the public URL + key."""
    client = _require_client()

    ext = ""
    if "." in original_filename:
        ext = "." + original_filename.split(".")[-1]

    mime_type, _ = mimetypes.guess_type(original_filename)
    if not mime_type:
        mime_type = "application/octet-stream"

    key = f"{folder}/{uuid.uuid4()}{ext}"

    if client is None:
        return {"url": f"https://mock.storage/{key}", "key": key}

    try:
        client.put_object(
            Bucket=settings.R2_BUCKET_NAME,
            Key=key,
            Body=file_content,
            ContentType=mime_type,
        )
    except ClientError as exc:
        raise RuntimeError(f"Failed to upload to R2: {exc}") from exc

    return {"url": f"{settings.R2_PUBLIC_URL}/{key}", "key": key}


def generate_presigned_url(
    folder: str,
    ext: str = ".mp4",
    mime: str = "video/mp4",
) -> dict:
    client = _require_client()

    ext_token = ext if ext.startswith(".") else f".{ext}"
    key = f"{folder}/{uuid.uuid4()}{ext_token}"

    if client is None:
        return {
            "presignedUrl": f"https://mock.storage/presign/{key}",
            "publicUrl": f"https://mock.storage/{key}",
            "key": key,
        }

    try:
        presigned = client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": settings.R2_BUCKET_NAME,
                "Key": key,
                "ContentType": mime,
            },
            ExpiresIn=3600,
        )
    except ClientError as exc:
        raise RuntimeError(f"Failed to generate presigned URL: {exc}") from exc

    return {
        "presignedUrl": presigned,
        "publicUrl": f"{settings.R2_PUBLIC_URL}/{key}",
        "key": key,
    }
