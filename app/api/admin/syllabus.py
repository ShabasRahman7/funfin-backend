from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from beanie import PydanticObjectId

from app.api.deps import get_admin_or_superadmin, get_editor_admin
from app.models.admin import Admin
from app.models.course import Course
from app.models.syllabus import Syllabus, SyllabusTopicEntry
from app.models.topic import Topic
from app.schemas.course import SyllabusCreate, SyllabusUpdate

router = APIRouter()


def _obj_id(raw: str, label: str = "id") -> PydanticObjectId:
    try:
        return PydanticObjectId(raw)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid {label}") from exc


async def _sync_course_module_count(course_id: PydanticObjectId) -> None:
    count = await Syllabus.find(Syllabus.course_id == course_id).count()
    course = await Course.get(course_id)
    if course is not None:
        course.total_modules = count
        await course.save()


async def _syllabus_public(s: Syllabus) -> dict:
    topic_ids = [t.topic_id for t in s.topics]
    topics_map = {}
    if topic_ids:
        topics = await Topic.find({"_id": {"$in": topic_ids}}).to_list()
        topics_map = {str(t.id): t.title for t in topics}

    return {
        "id": str(s.id),
        "courseId": str(s.course_id),
        "title": s.title,
        "moduleLabel": s.module_label,
        "coverImage": s.cover_image,
        "topics": [
            {"id": str(t.topic_id), "title": topics_map.get(str(t.topic_id), "")}
            for t in s.topics
        ],
        "createdAt": s.created_at,
        "updatedAt": s.updated_at,
    }


@router.post(
    "/syllabuses",
    status_code=status.HTTP_201_CREATED,
    summary="Create a syllabus module",
)
async def create_syllabus(
    payload: SyllabusCreate,
    admin: Admin = Depends(get_editor_admin),
):
    course_oid = _obj_id(payload.courseId, "courseId")
    course = await Course.get(course_oid)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    topic_entries = [
        SyllabusTopicEntry(
            topic_id=_obj_id(t.topicId, "topicId"),
            progress=t.progress or 0,
        )
        for t in (payload.topics or [])
    ]

    syllabus = Syllabus(
        course_id=course_oid,
        title=payload.title,
        module_label=payload.moduleLabel,
        cover_image=payload.coverImage,
        topics=topic_entries,
    )
    await syllabus.insert()

    await _sync_course_module_count(course_oid)

    return {
        "message": "Syllabus created successfully",
        "syllabus": await _syllabus_public(syllabus),
    }


@router.get(
    "/syllabuses",
    summary="List syllabuses (optionally filter by courseId)",
)
async def list_syllabuses(
    courseId: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=200),
    admin: Admin = Depends(get_admin_or_superadmin),
):
    query = {}
    if courseId:
        query["courseId"] = _obj_id(courseId, "courseId")

    total = await Syllabus.find(query).count()
    syllabuses = (
        await Syllabus.find(query)
        .sort(+Syllabus.created_at)
        .skip(skip)
        .limit(limit)
        .to_list()
    )
    public = [await _syllabus_public(s) for s in syllabuses]
    return {"syllabuses": public, "total": total}


@router.get(
    "/syllabuses/{syllabus_id}",
    summary="Get syllabus by ID",
)
async def get_syllabus(
    syllabus_id: str,
    admin: Admin = Depends(get_admin_or_superadmin),
):
    syllabus = await Syllabus.get(_obj_id(syllabus_id))
    if not syllabus:
        raise HTTPException(status_code=404, detail="Syllabus not found")
    return {"syllabus": await _syllabus_public(syllabus)}


@router.patch(
    "/syllabuses/{syllabus_id}",
    summary="Update a syllabus",
)
async def update_syllabus(
    syllabus_id: str,
    payload: SyllabusUpdate,
    admin: Admin = Depends(get_editor_admin),
):
    syllabus = await Syllabus.get(_obj_id(syllabus_id))
    if not syllabus:
        raise HTTPException(status_code=404, detail="Syllabus not found")

    if payload.title is not None:
        syllabus.title = payload.title
    if payload.moduleLabel is not None:
        syllabus.module_label = payload.moduleLabel
    if payload.coverImage is not None:
        syllabus.cover_image = payload.coverImage
    if payload.topics is not None:
        syllabus.topics = [
            SyllabusTopicEntry(
                topic_id=_obj_id(t.topicId, "topicId"),
                progress=t.progress or 0,
            )
            for t in payload.topics
        ]

    await syllabus.save()
    return {
        "message": "Syllabus updated successfully",
        "syllabus": await _syllabus_public(syllabus),
    }


@router.delete(
    "/syllabuses/{syllabus_id}",
    summary="Delete a syllabus",
)
async def delete_syllabus(
    syllabus_id: str,
    admin: Admin = Depends(get_admin_or_superadmin),
):
    syllabus = await Syllabus.get(_obj_id(syllabus_id))
    if not syllabus:
        raise HTTPException(status_code=404, detail="Syllabus not found")

    course_oid = syllabus.course_id
    await syllabus.delete()
    await _sync_course_module_count(course_oid)

    return {"message": "Syllabus deleted successfully"}
