from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.client import auth as client_auth
from app.api.client import course as client_course
from app.core.config import settings
from app.core.db import init_db


CLIENT_TAGS_METADATA = [
    {
        "name": "Auth",
        "description": "Authentication and account recovery",
    },
    {
        "name": "Courses",
        "description": "Course browsing and learning endpoints for clients.",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="LMS User Auth API",
    version="1.0.0",
    description="User authentication, OTP verification, and password recovery APIs.",
    openapi_tags=CLIENT_TAGS_METADATA,
    servers=[
        {"url": "http://localhost:5001", "description": "Local dev server"},
        {"url": "https://api-fun-fin.clt-academy.com", "description": "Client API server"},
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
    return {"message": "LMS client backend is healthy"}


app.include_router(client_auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(client_course.router, prefix="/api/v1", tags=["Courses"])


def _build_openapi_schema():
    if app.openapi_schema:
        return app.openapi_schema

    from fastapi.openapi.utils import get_openapi

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=CLIENT_TAGS_METADATA,
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
