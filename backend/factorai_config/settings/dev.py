"""
Local development settings.

Safe to run with zero external setup: falls back to a local SQLite file
when DATABASE_URL is not set, and ships permissive-but-not-insecure
dev-only defaults for SECRET_KEY / DEBUG / ALLOWED_HOSTS / CORS.
"""

import dj_database_url

from .base import *  # noqa: F401,F403
from .base import BASE_DIR, env

DEBUG = env.bool("DEBUG", default=True)

SECRET_KEY = env.str("SECRET_KEY", default="django-insecure-dev-only-secret-key")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# DATABASE_URL is optional in dev: no env var -> local SQLite, no external
# Postgres/TimescaleDB required to get the project running.
DATABASE_URL = env.str("DATABASE_URL", default=None)

if DATABASE_URL:
    DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)}

    # Tiger Cloud gotcha: its connection string omits the password. When
    # DB_PASSWORD is set, it overrides/fills whatever dj_database_url parsed.
    DB_PASSWORD = env.str("DB_PASSWORD", default="")
    if DB_PASSWORD:
        DATABASES["default"]["PASSWORD"] = DB_PASSWORD
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS", default=["http://localhost:3000", "http://127.0.0.1:3000"]
)
