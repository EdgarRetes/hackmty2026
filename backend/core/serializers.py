from rest_framework import serializers

from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    org_name = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ("role", "display_name", "org_name")

    def get_org_name(self, profile):
        if profile.role == UserProfile.Role.EMPRESA and profile.company:
            return profile.company.legal_name
        if profile.role == UserProfile.Role.FINANCIADORA and profile.lender:
            return profile.lender.name
        return ""
