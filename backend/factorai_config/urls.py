"""
Root URL configuration for factorai_config.

API-only backend: every app-facing response is JSON. The one exception is
/admin/, the built-in Django admin — an internal-only data management UI,
not a public-facing view. Each app should expose its own urls.py and get
included here under an /api/<app>/ prefix as endpoints are added.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("core.urls")),
]
