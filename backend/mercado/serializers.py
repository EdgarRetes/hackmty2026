from rest_framework import serializers

from .models import Offer


class LenderSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    risk_profile = serializers.CharField()


class OfferSerializer(serializers.ModelSerializer):
    lender = LenderSummarySerializer(read_only=True)

    class Meta:
        model = Offer
        fields = (
            "id",
            "invoice_id",
            "lender",
            "advance_percentage",
            "rate",
            "net_amount",
            "financing_cost",
            "funding_time",
            "category",
            "rank",
            "expires_at",
            "is_accepted",
        )
