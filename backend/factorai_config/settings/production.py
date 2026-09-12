"""
Production settings (Vultr, Docker, Gunicorn).

Everything sensitive comes from the environment — no dev-only fallbacks
here. Database is Postgres + TimescaleDB on Tiger Cloud.
"""

import dj_database_url

from .base import env
from .base import *  # noqa: F401,F403

DEBUG = env.bool("DEBUG", default=False)

SECRET_KEY = env.str("SECRET_KEY")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

DATABASES = {"default": dj_database_url.parse(env.str("DATABASE_URL"), conn_max_age=600)}

# Tiger Cloud gotcha: its DATABASE_URL never includes the password, so it
# must be supplied separately via DB_PASSWORD and merged in here. Without
# this, connections fail auth even though the URL "looks" complete.
DB_PASSWORD = env.str("DB_PASSWORD", default="")
if DB_PASSWORD:
    DATABASES["default"]["PASSWORD"] = DB_PASSWORD

DATABASES["default"]["OPTIONS"] = {"sslmode": "require"}

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS")

SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
