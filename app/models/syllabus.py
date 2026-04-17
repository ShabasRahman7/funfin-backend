from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from beanie import Document, PydanticObjectId


class SyllabusTopicEntry(BaseModel):
    topic_id: PydanticObjectId = Field(alias="topicId")
    progress: float = Field(default=0.0, ge=0, le=100)

    model_config = ConfigDict(populate_by_name=True)


class Syllabus(Document):
    course_id: PydanticObjectId = Field(alias="courseId")
    title: str
    module_label: str = Field(alias="moduleLabel")
    cover_image: Optional[str] = Field(default=None, alias="coverImage")
    topics: List[SyllabusTopicEntry] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True)

    class Settings:
        name = "syllabuses"
        indexes = ["courseId"]
