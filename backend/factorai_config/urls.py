"""
Root URL configuration for factorai_config.

API-only backend: every app-facing response is JSON. The one exception is
/admin/, the built-in Django admin — an internal-only data management UI,
not a public-facing view. Each app owns its own urls.py; routes are flat
REST resource paths under /api/ (no per-app prefix) — see API_CONTRACT.md
for the current endpoint list.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("core.urls")),
    path("api/", include("facturas.urls")),
    path("api/", include("mercado.urls")),
]
