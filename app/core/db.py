from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.models.admin import Admin
from app.models.course import Course
from app.models.interactions import Enrollment, Note, Review
from app.models.otp import OTP
from app.models.syllabus import Syllabus
from app.models.topic import Topic
from app.models.user import User


async def init_db() -> None:
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    database = client.get_default_database()

    await init_beanie(
        database=database,
        document_models=[
            User,
            Admin,
            OTP,
            Course,
            Syllabus,
            Topic,
            Enrollment,
            Review,
            Note,
        ],
    )
