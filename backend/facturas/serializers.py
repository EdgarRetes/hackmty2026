from datetime import date
from decimal import Decimal

from rest_framework import serializers

from .models import Invoice, InvoiceBatch


class CompanySummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    legal_name = serializers.CharField()
    rfc = serializers.CharField()


class DebtorClientSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    archetype = serializers.CharField()


class InvoiceSerializer(serializers.ModelSerializer):
    folio = serializers.SerializerMethodField()
    company = CompanySummarySerializer(read_only=True)
    debtor_client = DebtorClientSummarySerializer(read_only=True)
    days_until_due = serializers.SerializerMethodField()
    offers_count = serializers.IntegerField(read_only=True, default=0)
    batch_id = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = Invoice
        fields = (
            "id",
            "folio",
            "company",
            "debtor_client",
            "amount",
            "issue_date",
            "due_date",
            "status",
            "days_until_due",
            "offers_count",
            "batch_id",
        )

    def get_folio(self, invoice):
        return f"FAC-2026-{invoice.id:04d}"

    def get_days_until_due(self, invoice):
        return (invoice.due_date - date.today()).days


class InvoiceBatchSerializer(serializers.ModelSerializer):
    company = CompanySummarySerializer(read_only=True)
    invoices = InvoiceSerializer(many=True, read_only=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = InvoiceBatch
        fields = ("id", "company", "invoices", "total_amount", "created_at")

    def get_total_amount(self, batch):
        total = sum((invoice.amount for invoice in batch.invoices.all()), Decimal("0.00"))
        return str(total)
