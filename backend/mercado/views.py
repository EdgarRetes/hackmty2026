from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal
from uuid import uuid4

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from facturas.models import Invoice
from financiadoras.models import Lender

from .matching_engine import rank_offers
from .models import Offer
from .serializers import OfferSerializer


FUNDING_TIMES = {
    "conservative": "48 horas",
    "aggressive": "Hoy mismo",
    "specialized": "24 horas",
}


@api_view(["GET", "POST"])
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

    existing = Offer.objects.filter(invoice=invoice).select_related("lender")
    if request.method == "GET" or invoice.status == Invoice.Status.FUNDED:
        return Response(OfferSerializer(existing, many=True).data)

    ranked = rank_offers(invoice)
    expires_at = timezone.now() + timedelta(hours=24)
    rates = [Decimal(str(quote["rate"])) for quote in ranked]
    advances = [Decimal(str(quote["advance_percentage"])) for quote in ranked]
    amount = Decimal(str(invoice.amount))
    persisted = []

    with transaction.atomic():
        for index, quote in enumerate(ranked, start=1):
            lender_data = quote["lender"]
            lender, _ = Lender.objects.update_or_create(
                pk=lender_data["id"],
                defaults={
                    "name": lender_data["name"],
                    "risk_profile": lender_data["risk_profile"],
                    "is_verified": True,
                },
            )
            rate = Decimal(str(quote["rate"]))
            advance = Decimal(str(quote["advance_percentage"]))
            if index == 1:
                category = "best"
            elif rate == min(rates):
                category = "lowest_rate"
            elif advance == max(advances):
                category = "highest_advance"
            else:
                category = "fastest"
            financing_cost = (amount * rate / Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            offer = Offer.objects.filter(invoice=invoice, lender=lender).order_by("pk").first()
            if offer is None:
                offer = Offer(invoice=invoice, lender=lender)
            offer.advance_percentage = advance
            offer.rate = rate
            offer.net_amount = Decimal(str(quote["net_amount"]))
            offer.financing_cost = financing_cost
            offer.funding_time = FUNDING_TIMES[lender.risk_profile]
            offer.category = category
            offer.rank = index
            offer.expires_at = expires_at
            offer.save()
            persisted.append(offer)

    return Response(OfferSerializer(persisted, many=True).data)


@api_view(["POST"])
def accept_offer(request, offer_id):
    """Persist acceptance and mark the linked invoice as funded."""
    now = timezone.now()
    with transaction.atomic():
        try:
            offer = Offer.objects.select_for_update().select_related("invoice").get(pk=offer_id)
        except Offer.DoesNotExist:
            return Response({"detail": "Offer not found."}, status=status.HTTP_404_NOT_FOUND)
        if offer.is_accepted:
            return Response({"detail": "Offer already accepted."}, status=status.HTTP_409_CONFLICT)
        if offer.expires_at and offer.expires_at <= now:
            return Response({"detail": "Offer has expired."}, status=status.HTTP_409_CONFLICT)

        Offer.objects.filter(invoice=offer.invoice).exclude(pk=offer.pk).update(is_accepted=False, accepted_at=None)
        offer.is_accepted = True
        offer.accepted_at = now
        offer.save(update_fields=["is_accepted", "accepted_at"])
        offer.invoice.status = Invoice.Status.FUNDED
        offer.invoice.save(update_fields=["status"])

    return Response({
        "offer_id": offer.id,
        "invoice_id": offer.invoice_id,
        "status": "accepted",
        "transaction_id": f"TXN-{uuid4().hex[:12].upper()}",
        "accepted_at": now.isoformat(),
        "settlement_date": (now + timedelta(days=3)).date().isoformat(),
    })
