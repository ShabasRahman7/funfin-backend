# LMS Backend (Python + FastAPI + Beanie)

## Features
- Async FastAPI application with Pydantic request/response validation
- JWT bearer authentication
- User auth with OTP verification, social login, and password recovery
- Separate admin module (separate collection) with role-based CRUD
- Separate client/admin app instances and ports
- Swagger UI docs for user and admin APIs
- Layered structure (`app/api`, `app/models`, `app/schemas`, `app/core`, `app/scripts`)

## Setup

1. Create a virtual environment and install dependencies:
   - `python3 -m venv venv`
   - `source venv/bin/activate` (Windows: `venv\Scripts\activate`)
   - `pip install -r requirements.txt`
2. Copy env file:
   - `cp .env.example .env`
3. Run APIs:
   - Client only: `uvicorn app.client_main:app --reload --port 5001`
   - Admin only: `uvicorn app.admin_main:app --reload --port 5002`

## Env Keys

- `CLIENT_PORT` default `5001`
- `ADMIN_PORT` default `5002`
- `MONGODB_URI`, `JWT_SECRET`, `JWT_EXPIRES_IN` (e.g. `7d`)
- `MAIL_HOST`, `MAIL_PORT`, `MAIL_USER`, `MAIL_PASS`, `MAIL_FROM`
- `OTP_EXP_MINUTES`
- `FRONTEND_URL`, `ADMIN_URL` (CORS)
- `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`, `R2_PUBLIC_URL`
- `DEFAULT_ADMIN_EMAIL`, `DEFAULT_ADMIN_PASSWORD`, `DEFAULT_ADMIN_FULLNAME`, `DEFAULT_ADMIN_ROLE`

## Folder Structure

```text
app/
  api/
    client/     # client routers (auth, courses)
    admin/      # admin routers (auth, admins, courses, syllabus, topics, uploads)
    deps.py     # auth/role dependencies
  models/       # Beanie document models
  schemas/      # Pydantic request/response schemas
  core/         # config, db, security, mailer, storage
  scripts/      # seed/init scripts
  client_main.py  # client app entry
  admin_main.py   # admin app entry
```

## API Docs

- User/Auth docs: `http://localhost:5001/docs`
- Admin docs: `http://localhost:5002/docs`

## Main Routes

### User API (client process)
- `POST /api/v1/auth/signup`
- `POST /api/v1/auth/verify-otp`
- `POST /api/v1/auth/resend-otp`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/social-login` (`provider`: `google|apple`)
- `POST /api/v1/auth/forgot-password`
- `POST /api/v1/auth/reset-password`
- `GET  /api/v1/auth/profile`
- `GET  /api/v1/courses`
- `GET  /api/v1/courses/{courseId}/syllabus`
- `GET  /api/v1/topics/{id}`
- `POST /api/v1/topics/{id}/reviews`
- `POST /api/v1/topics/{id}/notes`

### Admin API (admin process)
- `POST /api/v1/admin-auth/bootstrap-superadmin`
- `POST /api/v1/admin-auth/login`
- `GET  /api/v1/admin-auth/profile`
- `POST /api/v1/admins`
- `GET  /api/v1/admins`
- `GET  /api/v1/admins/{id}`
- `PATCH /api/v1/admins/{id}`
- `DELETE /api/v1/admins/{id}`
- `POST /api/v1/courses`
- `GET  /api/v1/courses`
- `GET  /api/v1/courses/{id}`
- `PATCH /api/v1/courses/{id}`
- `DELETE /api/v1/courses/{id}`
- `POST /api/v1/syllabuses`
- `GET  /api/v1/syllabuses`
- `GET  /api/v1/syllabuses/{id}`
- `PATCH /api/v1/syllabuses/{id}`
- `DELETE /api/v1/syllabuses/{id}`
- `POST /api/v1/topics`
- `GET  /api/v1/topics`
- `GET  /api/v1/topics/{id}`
- `PATCH /api/v1/topics/{id}`
- `DELETE /api/v1/topics/{id}`
- `POST /api/v1/uploads/image`
- `POST /api/v1/uploads/video`
- `GET  /api/v1/uploads/video-presign`

## Seed Scripts

- Default admin: `python -m app.scripts.init_default_admin`
- Default courses: `python -m app.scripts.init_default_courses`
