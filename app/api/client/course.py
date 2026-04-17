from fastapi import APIRouter, Depends, HTTPException, status

from beanie import PydanticObjectId

from app.api.deps import get_current_user
from app.models.course import Course
from app.models.interactions import Enrollment, Note, Review
from app.models.syllabus import Syllabus
from app.models.topic import Topic
from app.models.user import User
from app.schemas.course import NoteCreate, ReviewCreate

router = APIRouter()


def _obj_id(raw: str, label: str = "id") -> PydanticObjectId:
    try:
        return PydanticObjectId(raw)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid {label}") from exc


@router.get(
    "/courses",
    summary="List all published courses with user enrollment status",
    description=(
        "Returns courses with title, photo, totalModules, duration, rating, "
        "and status (not_started | in_progress | completed)."
    ),
)
async def list_courses(current_user: User = Depends(get_current_user)):
    courses = (
        await Course.find(Course.is_published == True)  # noqa: E712
        .sort(-Course.created_at)
        .to_list()
    )

    enrollments = await Enrollment.find(
        Enrollment.user_id == current_user.id
    ).to_list()
    status_map = {str(e.course_id): e.status.value for e in enrollments}

    return {
        "courses": [
            {
                "id": str(c.id),
                "title": c.title,
                "photo": c.photo,
                "description": c.description,
                "totalModules": c.total_modules,
                "duration": c.duration,
                "rating": c.rating,
                "status": status_map.get(str(c.id), "not_started"),
            }
            for c in courses
        ]
    }


@router.get(
    "/courses/{course_id}/syllabus",
    summary="Get syllabus modules for a course",
)
async def get_syllabus(
    course_id: str,
    current_user: User = Depends(get_current_user),
):
    course_oid = _obj_id(course_id, "courseId")
    course = await Course.get(course_oid)
    if not course or not course.is_published:
        raise HTTPException(status_code=404, detail="Course not found")

    syllabuses = (
        await Syllabus.find(Syllabus.course_id == course_oid)
        .sort(+Syllabus.created_at)
        .to_list()
    )

    result = []
    for s in syllabuses:
        topic_ids = [entry.topic_id for entry in s.topics]
        topics = []
        if topic_ids:
            topics = (
                await Topic.find({"_id": {"$in": topic_ids}})
                .sort(+Topic.order)
                .to_list()
            )
        result.append(
            {
                "id": str(s.id),
                "title": s.title,
                "moduleLabel": s.module_label,
                "topics": [
                    {
                        "id": str(t.id),
                        "title": t.title,
                        "videoUrl": t.video_url,
                        "overview": t.overview,
                        "order": t.order,
                    }
                    for t in topics
                ],
            }
        )

    return {"courseId": course_id, "syllabus": result}


@router.get(
    "/topics/{topic_id}",
    summary="Get topic detail by ID (includes notes and reviews)",
)
async def get_topic_detail(
    topic_id: str,
    current_user: User = Depends(get_current_user),
):
    topic = await Topic.get(_obj_id(topic_id, "topicId"))
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    notes = await Note.find(Note.topic_id == topic.id).to_list()
    reviews = (
        await Review.find(Review.topic_id == topic.id)
        .sort(-Review.created_at)
        .to_list()
    )

    user_ids = {r.user_id for r in reviews}
    users_by_id: dict = {}
    if user_ids:
        users = await User.find({"_id": {"$in": list(user_ids)}}).to_list()
        users_by_id = {str(u.id): u for u in users}

    user_note = next((n for n in notes if str(n.user_id) == str(current_user.id)), None)

    return {
        "topic": {
            "id": str(topic.id),
            "title": topic.title,
            "videoUrl": topic.video_url,
            "overview": topic.overview,
            "order": topic.order,
        },
        "notes": [
            {
                "id": str(n.id),
                "userId": str(n.user_id),
                "content": n.content,
                "createdAt": n.created_at,
                "updatedAt": n.updated_at,
            }
            for n in notes
        ],
        "myNote": (
            {"id": str(user_note.id), "content": user_note.content}
            if user_note
            else None
        ),
        "reviews": [
            {
                "id": str(r.id),
                "user": (
                    {
                        "_id": str(r.user_id),
                        "fullName": users_by_id[str(r.user_id)].full_name,
                    }
                    if str(r.user_id) in users_by_id
                    else {"_id": str(r.user_id)}
                ),
                "rating": r.rating,
                "comment": r.comment,
                "createdAt": r.created_at,
            }
            for r in reviews
        ],
    }


@router.post(
    "/topics/{topic_id}/reviews",
    status_code=status.HTTP_201_CREATED,
    summary="Post or update a review for a topic",
)
async def post_review(
    topic_id: str,
    payload: ReviewCreate,
    current_user: User = Depends(get_current_user),
):
    topic = await Topic.get(_obj_id(topic_id, "topicId"))
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    review = await Review.find_one(
        Review.topic_id == topic.id, Review.user_id == current_user.id
    )
    if review:
        review.rating = payload.rating
        review.comment = payload.comment
        await review.save()
        return {
            "message": "Review updated successfully",
            "review": {
                "id": str(review.id),
                "topicId": str(review.topic_id),
                "userId": str(review.user_id),
                "rating": review.rating,
                "comment": review.comment,
                "createdAt": review.created_at,
                "updatedAt": review.updated_at,
            },
        }

    review = Review(
        topic_id=topic.id,
        user_id=current_user.id,
        rating=payload.rating,
        comment=payload.comment,
    )
    await review.insert()
    return {
        "message": "Review posted successfully",
        "review": {
            "id": str(review.id),
            "topicId": str(review.topic_id),
            "userId": str(review.user_id),
            "rating": review.rating,
            "comment": review.comment,
            "createdAt": review.created_at,
            "updatedAt": review.updated_at,
        },
    }


@router.post(
    "/topics/{topic_id}/notes",
    status_code=status.HTTP_201_CREATED,
    summary="Save or update personal notes for a topic",
)
async def save_note(
    topic_id: str,
    payload: NoteCreate,
    current_user: User = Depends(get_current_user),
):
    topic = await Topic.get(_obj_id(topic_id, "topicId"))
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    note = await Note.find_one(
        Note.topic_id == topic.id, Note.user_id == current_user.id
    )
    if note:
        note.content = payload.content
        await note.save()
        return {
            "message": "Note updated successfully",
            "note": {
                "id": str(note.id),
                "topicId": str(note.topic_id),
                "userId": str(note.user_id),
                "content": note.content,
                "createdAt": note.created_at,
                "updatedAt": note.updated_at,
            },
        }

    note = Note(topic_id=topic.id, user_id=current_user.id, content=payload.content)
    await note.insert()
    return {
        "message": "Note saved successfully",
        "note": {
            "id": str(note.id),
            "topicId": str(note.topic_id),
            "userId": str(note.user_id),
            "content": note.content,
            "createdAt": note.created_at,
            "updatedAt": note.updated_at,
        },
    }
