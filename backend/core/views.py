from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import UserProfile
from .serializers import UserProfileSerializer


@api_view(["GET"])
def health(request):
    return Response({"status": "ok", "service": "factorai-backend"})


@api_view(["GET"])
def profile_list(request):
    """
    The two demo role profiles (empresa / financiadora) the frontend's
    role switcher reads from — seeded via `manage.py seed_demo_data`.
    """
    profiles = UserProfile.objects.select_related("company", "lender")
    return Response(UserProfileSerializer(profiles, many=True).data)
