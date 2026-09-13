from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("profiles/", views.profile_list, name="profile-list"),
]
