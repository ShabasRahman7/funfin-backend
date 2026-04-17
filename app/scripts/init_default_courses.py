from __future__ import annotations

import asyncio

from app.core.db import init_db
from app.models.course import Course


_DEFAULT_COURSES = [
    {
        "title": "TradeCraft",
        "description": "Online Professional Stock Trading Course",
        "rating": 0,
        "duration": "8 weeks",
        "total_modules": 8,
        "is_published": True,
    },
    {
        "title": "Profit Code",
        "description": "Online Professional Stock Trading Course",
        "rating": 0,
        "duration": "14 weeks",
        "total_modules": 8,
        "is_published": True,
    },
    {
        "title": "CLT Vantage",
        "description": "Online Professional Stock Trading Course",
        "rating": 0,
        "duration": "8 weeks",
        "total_modules": 8,
        "is_published": True,
    },
]


async def run() -> None:
    await init_db()

    existing = await Course.find_all().count()
    if existing > 0:
        print(f"Courses already seeded ({existing} found). Skipping.")
        return

    docs = [Course(**c) for c in _DEFAULT_COURSES]
    await Course.insert_many(docs)
    print(f"Seeded {len(docs)} default courses.")


def main() -> None:
    try:
        asyncio.run(run())
    except Exception as exc:
        print(f"Default courses seed failed: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
