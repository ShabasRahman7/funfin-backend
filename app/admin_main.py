from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin import admin_mgmt
from app.api.admin import auth as admin_auth
from app.api.admin import course as admin_course
from app.api.admin import syllabus as admin_syllabus
from app.api.admin import topic as admin_topic
from app.api.admin import upload as admin_upload
from app.core.config import settings
from app.core.db import init_db


ADMIN_TAGS_METADATA = [
    {
        "name": "Admin Auth",
        "description": "Authentication endpoints for admin panel users.",
    },
    {
        "name": "Admin Management",
        "description": "Role-based CRUD endpoints for admin users.",
    },
    {
        "name": "Admin Courses",
        "description": "Course management endpoints for admin panel.",
    },
    {
        "name": "Admin Syllabus",
        "description": "Syllabus management endpoints for admin panel.",
    },
    {
        "name": "Admin Topics",
        "description": "Topic management endpoints for admin panel.",
    },
    {
        "name": "Uploads",
        "description": "Media upload endpoints for admin panel.",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="LMS Admin API",
    version="1.0.0",
    description="Admin authentication and admin CRUD APIs (separate admin collection).",
    openapi_tags=ADMIN_TAGS_METADATA,
    servers=[
        {"url": "http://localhost:5002", "description": "Local dev server"},
        {"url": "https://api-admin-fun-fin.clt-academy.com", "description": "Admin API server"},
    ],
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "PUT", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/health", include_in_schema=False)
def health():
    return {"message": "LMS admin backend is healthy"}


app.include_router(admin_auth.router, prefix="/api/v1/admin-auth", tags=["Admin Auth"])
app.include_router(admin_mgmt.router, prefix="/api/v1/admins", tags=["Admin Management"])
app.include_router(admin_course.router, prefix="/api/v1", tags=["Admin Courses"])
app.include_router(admin_syllabus.router, prefix="/api/v1", tags=["Admin Syllabus"])
app.include_router(admin_topic.router, prefix="/api/v1", tags=["Admin Topics"])
app.include_router(admin_upload.router, prefix="/api/v1/uploads", tags=["Uploads"])


def _build_openapi_schema():
    if app.openapi_schema:
        return app.openapi_schema

    from fastapi.openapi.utils import get_openapi

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=ADMIN_TAGS_METADATA,
        servers=app.servers,
    )
    components = schema.setdefault("components", {})
    components.setdefault("securitySchemes", {})["bearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Paste JWT token as: Bearer <token>",
    }
    app.openapi_schema = schema
    return schema


app.openapi = _build_openapi_schema
