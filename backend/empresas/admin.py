from django.contrib import admin

from .models import Company, DebtorClient, PaymentHistory


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("rfc", "legal_name", "is_verified", "nessie_account_id")


@admin.register(DebtorClient)
class DebtorClientAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "archetype")


@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = ("debtor_client", "amount", "days_late", "paid_at", "nessie_deposit_id")
