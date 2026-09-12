from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal
from uuid import uuid4

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from facturas.fixtures import get_invoice

from .fixtures import LENDER_OFFER_TEMPLATES


def _money(value):
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


@api_view(["POST"])
def create_offers(request, invoice_id):
    """
    TEMPORARY: returns hardcoded example offers instead of running the
    real bidding logic. See API_CONTRACT.md.
    """
    invoice = get_invoice(invoice_id)
    if invoice is None:
        return Response(
            {"detail": "Invoice not found."}, status=status.HTTP_404_NOT_FOUND
        )

    amount = Decimal(invoice["amount"])
    expires_at = timezone.now() + timedelta(hours=24)

    offers = [
        {
            "id": invoice_id * 100 + index,
            "invoice_id": invoice_id,
            "lender": template["lender"],
            "advance_percentage": template["advance_percentage"],
            "rate": template["rate"],
            "net_amount": _money(amount * Decimal(template["advance_percentage"]) / 100),
            "expires_at": expires_at.isoformat(),
        }
        for index, template in enumerate(LENDER_OFFER_TEMPLATES, start=1)
    ]

    return Response(offers)


@api_view(["POST"])
def accept_offer(request, offer_id):
    """
    TEMPORARY: always succeeds and fabricates a transaction_id instead of
    persisting a real acceptance. See API_CONTRACT.md.
    """
    now = timezone.now()

    return Response(
        {
            "offer_id": offer_id,
            "invoice_id": offer_id // 100 if offer_id >= 100 else None,
            "status": "accepted",
            "transaction_id": f"TXN-{uuid4().hex[:12].upper()}",
            "accepted_at": now.isoformat(),
            "settlement_date": (now + timedelta(days=3)).date().isoformat(),
        }
    )
