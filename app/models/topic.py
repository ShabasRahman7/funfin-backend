from datetime import datetime

from pydantic import ConfigDict, Field

from beanie import Document, PydanticObjectId


class Topic(Document):
    syllabus_id: PydanticObjectId = Field(alias="syllabusId")
    course_id: PydanticObjectId = Field(alias="courseId")
    title: str
    video_url: str = Field(alias="videoUrl")
    overview: str
    order: int = 0

    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True)

    class Settings:
        name = "topics"
        indexes = ["syllabusId", "courseId"]
