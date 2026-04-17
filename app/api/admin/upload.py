from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from app.api.deps import get_current_admin
from app.core.storage import generate_presigned_url, upload_to_r2
from app.models.admin import Admin

router = APIRouter()


_IMAGE_SIZE_LIMIT = 10 * 1024 * 1024  # 10 MB
_VIDEO_SIZE_LIMIT = 500 * 1024 * 1024  # 500 MB


async def _read_file_bounded(file: UploadFile, max_bytes: int) -> bytes:
    data = await file.read()
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum size of {max_bytes // (1024 * 1024)} MB",
        )
    return data


@router.post(
    "/image",
    summary="Upload an image (course photo, syllabus cover, etc.)",
)
async def upload_image(
    file: UploadFile = File(...),
    admin: Admin = Depends(get_current_admin),
):
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    data = await _read_file_bounded(file, _IMAGE_SIZE_LIMIT)

    try:
        result = upload_to_r2(data, file.filename or "image", folder="images")
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to upload image: {exc}"
        ) from exc

    return {
        "url": result["url"],
        "public_id": result["key"],
        "message": "Image uploaded successfully",
    }


@router.post(
    "/video",
    summary="Upload a video (topic video)",
)
async def upload_video(
    file: UploadFile = File(...),
    admin: Admin = Depends(get_current_admin),
):
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    if not (file.content_type or "").startswith("video/"):
        raise HTTPException(status_code=400, detail="Only video files are allowed")

    data = await _read_file_bounded(file, _VIDEO_SIZE_LIMIT)

    try:
        result = upload_to_r2(data, file.filename or "video", folder="videos")
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to upload video: {exc}"
        ) from exc

    return {
        "url": result["url"],
        "public_id": result["key"],
        "message": "Video uploaded successfully",
    }


@router.get(
    "/video-presign",
    summary="Get pre-signed URL for direct browser-to-R2 video upload",
)
async def get_video_presigned_url(
    ext: str = Query(".mp4"),
    mime: str = Query("video/mp4"),
    admin: Admin = Depends(get_current_admin),
):
    try:
        return generate_presigned_url(folder="videos", ext=ext, mime=mime)
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate presigned URL: {exc}"
        ) from exc
