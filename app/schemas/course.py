from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CourseCreate(BaseModel):
    title: str = Field(min_length=2)
    photo: Optional[str] = None
    videoUrl: Optional[str] = None
    description: str = Field(min_length=10)
    rating: Optional[float] = Field(default=None, ge=0, le=5)
    duration: str = Field(min_length=1)
    totalModules: Optional[int] = Field(default=None, ge=0)
    isPublished: Optional[bool] = None

    @model_validator(mode="after")
    def _at_least_photo_or_video(self) -> "CourseCreate":
        if not (self.photo or self.videoUrl):
            raise ValueError("At least one of photo or videoUrl is required")
        return self


class CourseUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2)
    photo: Optional[str] = None
    videoUrl: Optional[str] = None
    description: Optional[str] = Field(default=None, min_length=10)
    rating: Optional[float] = Field(default=None, ge=0, le=5)
    duration: Optional[str] = Field(default=None, min_length=1)
    totalModules: Optional[int] = Field(default=None, ge=0)
    isPublished: Optional[bool] = None

    @model_validator(mode="after")
    def _not_empty(self) -> "CourseUpdate":
        if not any(
            getattr(self, f) is not None
            for f in (
                "title",
                "photo",
                "videoUrl",
                "description",
                "rating",
                "duration",
                "totalModules",
                "isPublished",
            )
        ):
            raise ValueError("At least one field must be provided")
        return self


class SyllabusTopicInput(BaseModel):
    topicId: str
    progress: Optional[float] = Field(default=0, ge=0, le=100)


class SyllabusCreate(BaseModel):
    courseId: str = Field(min_length=1)
    title: str = Field(min_length=2)
    moduleLabel: str = Field(min_length=1)
    coverImage: Optional[str] = None
    topics: Optional[List[SyllabusTopicInput]] = Field(default_factory=list)


class SyllabusUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2)
    moduleLabel: Optional[str] = Field(default=None, min_length=1)
    coverImage: Optional[str] = None
    topics: Optional[List[SyllabusTopicInput]] = None

    @model_validator(mode="after")
    def _not_empty(self) -> "SyllabusUpdate":
        if not any(
            getattr(self, f) is not None
            for f in ("title", "moduleLabel", "coverImage", "topics")
        ):
            raise ValueError("At least one field must be provided")
        return self


class TopicCreate(BaseModel):
    syllabusId: str = Field(min_length=1)
    courseId: str = Field(min_length=1)
    title: str = Field(min_length=2)
    videoUrl: str = Field(min_length=1)
    overview: str = Field(min_length=10)
    order: Optional[int] = Field(default=0, ge=0)


class TopicUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2)
    videoUrl: Optional[str] = Field(default=None, min_length=1)
    overview: Optional[str] = Field(default=None, min_length=10)
    order: Optional[int] = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _not_empty(self) -> "TopicUpdate":
        if not any(
            getattr(self, f) is not None
            for f in ("title", "videoUrl", "overview", "order")
        ):
            raise ValueError("At least one field must be provided")
        return self


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str = Field(min_length=1)


class NoteCreate(BaseModel):
    content: str = Field(min_length=1)
