"""
Base settings shared by every environment.

Nothing environment-specific (DEBUG, SECRET_KEY, DATABASE_URL, allowed hosts,
CORS origins) lives here — see dev.py / production.py, which both import
this module and layer environment reads on top via django-environ.
"""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    # No admin/sessions/messages/staticfiles: this backend is API-only,
    # JSON in and out, no server-rendered templates or session-based UI.
    "rest_framework",
    "corsheaders",
    "empresas",
    "financiadoras",
    "facturas",
    "mercado",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "factorai_config.urls"

# No TEMPLATES setting: API-only backend, never add template rendering here.

WSGI_APPLICATION = "factorai_config.wsgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/Mexico_City"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}
