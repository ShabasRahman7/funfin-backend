from datetime import datetime
from enum import Enum

from pydantic import ConfigDict, Field

from beanie import Document, PydanticObjectId


class EnrollmentStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Enrollment(Document):
    user_id: PydanticObjectId = Field(alias="userId")
    course_id: PydanticObjectId = Field(alias="courseId")
    status: EnrollmentStatus = EnrollmentStatus.NOT_STARTED

    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True)

    class Settings:
        name = "enrollments"
        indexes = [
            [("userId", 1), ("courseId", 1)],
        ]


class Review(Document):
    topic_id: PydanticObjectId = Field(alias="topicId")
    user_id: PydanticObjectId = Field(alias="userId")
    rating: int = Field(ge=1, le=5)
    comment: str

    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True)

    class Settings:
        name = "reviews"
        indexes = [
            [("topicId", 1), ("userId", 1)],
        ]


class Note(Document):
    topic_id: PydanticObjectId = Field(alias="topicId")
    user_id: PydanticObjectId = Field(alias="userId")
    content: str

    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True)

    class Settings:
        name = "notes"
        indexes = [
            [("topicId", 1), ("userId", 1)],
        ]
