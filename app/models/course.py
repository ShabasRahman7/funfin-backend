from datetime import datetime
from typing import Optional

from pydantic import ConfigDict, Field

from beanie import Document


class Course(Document):
    title: str
    photo: Optional[str] = None
    video_url: Optional[str] = Field(default=None, alias="videoUrl")
    description: str
    rating: float = Field(default=0.0, ge=0, le=5)
    duration: str
    total_modules: int = Field(default=0, alias="totalModules")
    is_published: bool = Field(default=False, alias="isPublished")

    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True)

    class Settings:
        name = "courses"
