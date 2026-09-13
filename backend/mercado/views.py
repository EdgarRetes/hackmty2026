from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal
from uuid import uuid4

from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.risk_engine import assess_invoice
from facturas.models import Invoice, InvoiceBatch, RiskAssessment
from facturas.serializers import RiskAssessmentSerializer
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

    assessment = assess_invoice(invoice)
    if assessment.decision != RiskAssessment.Decision.APPROVE:
        existing.delete()
        return Response(
            {
                "detail": "Invoice did not pass automatic underwriting.",
                "assessment": RiskAssessmentSerializer(assessment).data,
            },
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    ranked = rank_offers(invoice, assessment)
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
            financing_cost = Decimal(str(quote["financing_cost"]))
            offer = Offer.objects.filter(invoice=invoice, lender=lender).order_by("pk").first()
            if offer is None:
                offer = Offer(invoice=invoice, lender=lender)
            offer.advance_percentage = advance
            offer.rate = rate
            offer.risk_assessment = assessment
            offer.net_amount = Decimal(str(quote["net_amount"]))
            offer.financing_cost = financing_cost
            offer.funding_time = FUNDING_TIMES[lender.risk_profile]
            offer.category = category
            offer.rank = index
            offer.expires_at = expires_at
            offer.save()
            persisted.append(offer)

    return Response(OfferSerializer(persisted, many=True).data)


def _money(value):
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


@api_view(["GET"])
def batch_offers(request, batch_id):
    """
    Aggregated offers for a published InvoiceBatch: runs the exact same
    per-invoice pipeline (risk engine + 3 pricing agents + matching
    engine) on every invoice in the batch, then combines each lender's
    quotes across all of them into one package-level offer — net_amount
    summed, rate/advance_percentage amount-weighted-averaged. Computed on
    request, not persisted (unlike single-invoice offers, which are).
    See API_CONTRACT.md.
    """
    try:
        batch = InvoiceBatch.objects.prefetch_related(
            Prefetch(
                "invoices",
                queryset=Invoice.objects.select_related("company", "debtor_client"),
            )
        ).get(pk=batch_id)
    except InvoiceBatch.DoesNotExist:
        return Response({"detail": "Batch not found."}, status=status.HTTP_404_NOT_FOUND)

    invoices = list(batch.invoices.all())
    if not invoices:
        return Response({"detail": "Batch has no invoices."}, status=status.HTTP_400_BAD_REQUEST)

    buckets = {}
    for invoice in invoices:
        amount = Decimal(str(invoice.amount))
        assessment = assess_invoice(invoice)
        if assessment.decision != RiskAssessment.Decision.APPROVE:
            return Response(
                {
                    "detail": "One or more invoices did not pass automatic underwriting.",
                    "invoice_id": invoice.id,
                    "assessment": RiskAssessmentSerializer(assessment).data,
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        for quote in rank_offers(invoice, assessment):
            lender_id = quote["lender"]["id"]
            bucket = buckets.setdefault(
                lender_id,
                {
                    "lender": quote["lender"],
                    "net_amount": Decimal("0"),
                    "weighted_rate": Decimal("0"),
                    "weighted_advance": Decimal("0"),
                    "financing_cost": Decimal("0"),
                    "total_amount": Decimal("0"),
                },
            )
            bucket["net_amount"] += Decimal(quote["net_amount"])
            bucket["weighted_rate"] += Decimal(quote["rate"]) * amount
            bucket["weighted_advance"] += Decimal(quote["advance_percentage"]) * amount
            bucket["financing_cost"] += Decimal(quote["financing_cost"])
            bucket["total_amount"] += amount

    aggregated = []
    for bucket in buckets.values():
        total_amount = bucket["total_amount"]
        aggregated.append(
            {
                "lender": bucket["lender"],
                "advance_percentage": _money(bucket["weighted_advance"] / total_amount),
                "rate": _money(bucket["weighted_rate"] / total_amount),
                "net_amount": _money(bucket["net_amount"]),
                "financing_cost": _money(bucket["financing_cost"]),
            }
        )
    aggregated.sort(key=lambda q: (-Decimal(q["net_amount"]), Decimal(q["rate"])))

    rates = [Decimal(q["rate"]) for q in aggregated]
    advances = [Decimal(q["advance_percentage"]) for q in aggregated]
    expires_at = timezone.now() + timedelta(hours=24)

    offers = []
    for index, quote in enumerate(aggregated, start=1):
        rate = Decimal(quote["rate"])
        advance = Decimal(quote["advance_percentage"])
        if index == 1:
            category = "best"
        elif rate == min(rates):
            category = "lowest_rate"
        elif advance == max(advances):
            category = "highest_advance"
        else:
            category = "fastest"
        offers.append(
            {
                "id": batch_id * 100 + index,
                "batch_id": batch_id,
                "lender": quote["lender"],
                "advance_percentage": quote["advance_percentage"],
                "rate": quote["rate"],
                "net_amount": quote["net_amount"],
                "financing_cost": quote["financing_cost"],
                "funding_time": FUNDING_TIMES[quote["lender"]["risk_profile"]],
                "category": category,
                "rank": index,
                "expires_at": expires_at.isoformat(),
            }
        )

    return Response(offers)


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
