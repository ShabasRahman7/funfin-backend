from fastapi import APIRouter, Depends, HTTPException, Query, status

from beanie import PydanticObjectId

from app.api.deps import get_admin_or_superadmin, get_editor_admin
from app.models.admin import Admin
from app.models.course import Course
from app.schemas.course import CourseCreate, CourseUpdate

router = APIRouter()


def _course_public(c: Course) -> dict:
    return {
        "id": str(c.id),
        "title": c.title,
        "photo": c.photo,
        "videoUrl": c.video_url,
        "description": c.description,
        "rating": c.rating,
        "duration": c.duration,
        "totalModules": c.total_modules,
        "isPublished": c.is_published,
        "createdAt": c.created_at,
        "updatedAt": c.updated_at,
    }


def _obj_id(raw: str) -> PydanticObjectId:
    try:
        return PydanticObjectId(raw)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid course id") from exc


@router.post(
    "/courses",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new course",
)
async def create_course(
    payload: CourseCreate,
    admin: Admin = Depends(get_editor_admin),
):
    course = Course(
        title=payload.title,
        photo=payload.photo,
        video_url=payload.videoUrl,
        description=payload.description,
        rating=payload.rating if payload.rating is not None else 0,
        duration=payload.duration,
        total_modules=payload.totalModules or 0,
        is_published=payload.isPublished if payload.isPublished is not None else False,
    )
    await course.insert()
    return {"message": "Course created successfully", "course": _course_public(course)}


@router.get(
    "/courses",
    summary="List all courses",
)
async def list_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=200),
    admin: Admin = Depends(get_admin_or_superadmin),
):
    total = await Course.find().count()
    courses = (
        await Course.find()
        .sort(-Course.created_at)
        .skip(skip)
        .limit(limit)
        .to_list()
    )
    return {"courses": [_course_public(c) for c in courses], "total": total}


@router.get(
    "/courses/{course_id}",
    summary="Get course by ID",
)
async def get_course(
    course_id: str,
    admin: Admin = Depends(get_admin_or_superadmin),
):
    course = await Course.get(_obj_id(course_id))
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"course": _course_public(course)}


@router.patch(
    "/courses/{course_id}",
    summary="Update a course",
)
async def update_course(
    course_id: str,
    payload: CourseUpdate,
    admin: Admin = Depends(get_editor_admin),
):
    course = await Course.get(_obj_id(course_id))
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if payload.title is not None:
        course.title = payload.title
    if payload.photo is not None:
        course.photo = payload.photo
    if payload.videoUrl is not None:
        course.video_url = payload.videoUrl
    if payload.description is not None:
        course.description = payload.description
    if payload.rating is not None:
        course.rating = payload.rating
    if payload.duration is not None:
        course.duration = payload.duration
    if payload.totalModules is not None:
        course.total_modules = payload.totalModules
    if payload.isPublished is not None:
        course.is_published = payload.isPublished

    await course.save()
    return {"message": "Course updated successfully", "course": _course_public(course)}


@router.delete(
    "/courses/{course_id}",
    summary="Delete a course",
)
async def delete_course(
    course_id: str,
    admin: Admin = Depends(get_admin_or_superadmin),
):
    course = await Course.get(_obj_id(course_id))
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    await course.delete()
    return {"message": "Course deleted successfully"}
