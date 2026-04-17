from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from beanie import PydanticObjectId

from app.api.deps import get_admin_or_superadmin, get_editor_admin
from app.models.admin import Admin
from app.models.syllabus import Syllabus, SyllabusTopicEntry
from app.models.topic import Topic
from app.schemas.course import TopicCreate, TopicUpdate

router = APIRouter()


def _obj_id(raw: str, label: str = "id") -> PydanticObjectId:
    try:
        return PydanticObjectId(raw)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid {label}") from exc


def _topic_public(t: Topic) -> dict:
    return {
        "id": str(t.id),
        "syllabusId": str(t.syllabus_id),
        "courseId": str(t.course_id),
        "title": t.title,
        "videoUrl": t.video_url,
        "overview": t.overview,
        "order": t.order,
        "createdAt": t.created_at,
        "updatedAt": t.updated_at,
    }


@router.post(
    "/topics",
    status_code=status.HTTP_201_CREATED,
    summary="Create a topic",
)
async def create_topic(
    payload: TopicCreate,
    admin: Admin = Depends(get_editor_admin),
):
    syllabus_oid = _obj_id(payload.syllabusId, "syllabusId")
    course_oid = _obj_id(payload.courseId, "courseId")

    syllabus = await Syllabus.get(syllabus_oid)
    if not syllabus:
        raise HTTPException(status_code=404, detail="Syllabus not found")

    topic = Topic(
        syllabus_id=syllabus_oid,
        course_id=course_oid,
        title=payload.title,
        video_url=payload.videoUrl,
        overview=payload.overview,
        order=payload.order or 0,
    )
    await topic.insert()

    already = any(str(t.topic_id) == str(topic.id) for t in syllabus.topics)
    if not already:
        syllabus.topics.append(
            SyllabusTopicEntry(topic_id=topic.id, progress=0)
        )
        await syllabus.save()

    return {"message": "Topic created successfully", "topic": _topic_public(topic)}


@router.get(
    "/topics",
    summary="List topics (filter by syllabusId or courseId)",
)
async def list_topics(
    syllabusId: Optional[str] = Query(None),
    courseId: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    admin: Admin = Depends(get_admin_or_superadmin),
):
    query = {}
    if syllabusId:
        query["syllabusId"] = _obj_id(syllabusId, "syllabusId")
    if courseId:
        query["courseId"] = _obj_id(courseId, "courseId")

    total = await Topic.find(query).count()
    topics = (
        await Topic.find(query)
        .sort(+Topic.order)
        .skip(skip)
        .limit(limit)
        .to_list()
    )
    return {"topics": [_topic_public(t) for t in topics], "total": total}


@router.get(
    "/topics/{topic_id}",
    summary="Get topic by ID",
)
async def get_topic(
    topic_id: str,
    admin: Admin = Depends(get_admin_or_superadmin),
):
    topic = await Topic.get(_obj_id(topic_id))
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return {"topic": _topic_public(topic)}


@router.patch(
    "/topics/{topic_id}",
    summary="Update a topic",
)
async def update_topic(
    topic_id: str,
    payload: TopicUpdate,
    admin: Admin = Depends(get_editor_admin),
):
    topic = await Topic.get(_obj_id(topic_id))
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    if payload.title is not None:
        topic.title = payload.title
    if payload.videoUrl is not None:
        topic.video_url = payload.videoUrl
    if payload.overview is not None:
        topic.overview = payload.overview
    if payload.order is not None:
        topic.order = payload.order

    await topic.save()
    return {"message": "Topic updated successfully", "topic": _topic_public(topic)}


@router.delete(
    "/topics/{topic_id}",
    summary="Delete a topic",
)
async def delete_topic(
    topic_id: str,
    admin: Admin = Depends(get_admin_or_superadmin),
):
    topic_oid = _obj_id(topic_id)
    topic = await Topic.get(topic_oid)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    syllabus = await Syllabus.get(topic.syllabus_id)
    if syllabus is not None:
        syllabus.topics = [
            entry for entry in syllabus.topics if str(entry.topic_id) != str(topic_oid)
        ]
        await syllabus.save()

    await topic.delete()
    return {"message": "Topic deleted successfully"}
