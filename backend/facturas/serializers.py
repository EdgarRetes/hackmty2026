from datetime import date
from decimal import Decimal

from rest_framework import serializers

from .models import Invoice, InvoiceBatch, RiskAssessment


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
        fields = ("id", "company", "invoices", "total_amount", "factoring_term_days", "created_at")

    def get_total_amount(self, batch):
        total = sum((invoice.amount for invoice in batch.invoices.all()), Decimal("0.00"))
        return str(total)


class RiskAssessmentSerializer(serializers.ModelSerializer):
    reason_codes = serializers.SerializerMethodField()

    class Meta:
        model = RiskAssessment
        fields = (
            "id", "invoice_id", "decision", "rating", "risk_score",
            "probability_of_default", "loss_given_default", "exposure_at_default",
            "expected_default_loss", "expected_dilution_loss", "expected_loss",
            "confidence", "term_days", "reference_rate", "reference_rate_as_of",
            "reference_rate_source", "recommended_annual_rate",
            "recommended_monthly_rate", "recommended_advance_percentage",
            "financing_cost", "net_disbursement", "expected_investor_profit",
            "reasons", "reason_codes", "warnings", "input_snapshot",
            "policy_version", "created_at",
        )

    def get_reason_codes(self, assessment):
        return assessment.input_snapshot.get("reason_codes", [])
