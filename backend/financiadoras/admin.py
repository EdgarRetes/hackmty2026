from django.contrib import admin

from .models import Lender


@admin.register(Lender)
class LenderAdmin(admin.ModelAdmin):
    list_display = ("name", "risk_profile", "is_verified", "nessie_account_id")
