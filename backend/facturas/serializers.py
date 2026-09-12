from datetime import date

from rest_framework import serializers

from .models import Invoice


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
        )

    def get_folio(self, invoice):
        return f"FAC-2026-{invoice.id:04d}"

    def get_days_until_due(self, invoice):
        return (invoice.due_date - date.today()).days
