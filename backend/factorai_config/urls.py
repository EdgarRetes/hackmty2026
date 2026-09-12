"""
Root URL configuration for factorai_config.

API-only backend: no admin site, no templates. Each app should expose its
own urls.py and get included here under an /api/<app>/ prefix as endpoints
are added.
"""

from django.urls import include, path

urlpatterns = [
    path("api/", include("core.urls")),
]
