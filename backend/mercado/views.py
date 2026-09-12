from datetime import timedelta
from uuid import uuid4

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from facturas.models import Invoice

from .matching_engine import rank_offers


@api_view(["POST"])
def create_offers(request, invoice_id):
    """
    Runs the invoice through the risk engine, all three pricing agents,
    and the matching engine, then returns the ranked offers (best net
    cash to the empresa first). See API_CONTRACT.md.
    """
    try:
        invoice = Invoice.objects.select_related("company", "debtor_client").get(
            pk=invoice_id
        )
    except Invoice.DoesNotExist:
        return Response(
            {"detail": "Invoice not found."}, status=status.HTTP_404_NOT_FOUND
        )

    ranked = rank_offers(invoice)
    expires_at = timezone.now() + timedelta(hours=24)

    offers = [
        {
            "id": invoice_id * 100 + index,
            "invoice_id": invoice_id,
            "lender": quote["lender"],
            "advance_percentage": quote["advance_percentage"],
            "rate": quote["rate"],
            "net_amount": quote["net_amount"],
            "expires_at": expires_at.isoformat(),
        }
        for index, quote in enumerate(ranked, start=1)
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
