from django.contrib import admin

from .models import Invoice


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "company",
        "debtor_client",
        "amount",
        "issue_date",
        "due_date",
        "status",
    )
