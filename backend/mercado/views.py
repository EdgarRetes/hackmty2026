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

from .matching_engine import opportunity_summary, rank_offers
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


@api_view(["GET"])
def marketplace_opportunities(request):
    """
    Every published, still-open publicación (InvoiceBatch — 1 or more
    invoices) as a Financiadora-facing opportunity: aggregate amount,
    risk engine + pricing agent output (risk bucket, estimated return),
    sector, and whether any of its debtors has been financed before.
    See API_CONTRACT.md.
    """
    batches = InvoiceBatch.objects.select_related("company").prefetch_related(
        Prefetch(
            "invoices", queryset=Invoice.objects.select_related("company", "debtor_client")
        )
    ).order_by("-created_at")

    risk_rank = {"low": 0, "medium": 1, "high": 2}
    opportunities = []

    for batch in batches:
        invoices = list(batch.invoices.all())
        open_invoices = [
            inv for inv in invoices
            if inv.status in (Invoice.Status.PENDING, Invoice.Status.IN_AUCTION)
        ]
        if not open_invoices:
            continue

        amount = sum((Decimal(str(inv.amount)) for inv in invoices), Decimal("0"))
        summaries = [opportunity_summary(inv) for inv in invoices]
        risk = max((s["risk"] for s in summaries), key=lambda r: risk_rank[r])
        avg_return_rate = (
            sum(Decimal(s["estimated_return_rate"]) for s in summaries) / len(summaries)
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total_return = sum((Decimal(s["estimated_return"]) for s in summaries), Decimal("0"))
        sectors = {s["sector"] for s in summaries if s["sector"]}
        sector = next(iter(sectors)) if len(sectors) == 1 else None

        debtor_ids = {inv.debtor_client_id for inv in invoices}
        debtor_names = sorted({inv.debtor_client.name for inv in invoices})
        previously_financed = Invoice.objects.filter(
            debtor_client_id__in=debtor_ids,
            status__in=[Invoice.Status.FUNDED, Invoice.Status.PAID],
        ).exclude(pk__in=[inv.pk for inv in invoices]).exists()

        earliest_due = min(inv.due_date for inv in invoices)
        today = timezone.now().date()

        opportunities.append(
            {
                "id": batch.id,
                "folio": (
                    f"FAC-2026-{invoices[0].id:04d}"
                    if len(invoices) == 1
                    else f"PUB-{batch.id:04d}"
                ),
                "invoice_count": len(invoices),
                "company": {
                    "id": batch.company_id,
                    "legal_name": batch.company.legal_name,
                    "rfc": batch.company.rfc,
                },
                "debtor": debtor_names[0] if len(debtor_names) == 1 else f"{len(debtor_names)} deudores",
                "amount": str(amount),
                "issue_date": min(inv.issue_date for inv in invoices).isoformat(),
                "due_date": earliest_due.isoformat(),
                "days_until_due": (earliest_due - today).days,
                "sector": sector,
                "risk": risk,
                "estimated_return_rate": str(avg_return_rate),
                "estimated_return": str(total_return),
                "previously_financed": previously_financed,
            }
        )

    lender = Lender.objects.order_by("id").first()
    available_capital = str(lender.available_capital) if lender else "0"

    return Response({"opportunities": opportunities, "available_capital": available_capital})


@api_view(["POST"])
def accept_batch_offer(request, batch_id):
    """
    A financiadora accepting a publicación: persists a real Offer for
    the chosen lender on every invoice in the batch (reusing the same
    per-invoice pricing already computed for the single-invoice flow),
    marks them all accepted, and funds every invoice in the batch at
    once. Body: {"lender_id": <id>}.
    """
    try:
        batch = InvoiceBatch.objects.prefetch_related(
            Prefetch(
                "invoices",
                queryset=Invoice.objects.select_related("company", "debtor_client"),
            )
        ).get(pk=batch_id)
    except InvoiceBatch.DoesNotExist:
        return Response({"detail": "Publication not found."}, status=status.HTTP_404_NOT_FOUND)

    invoices = list(batch.invoices.all())
    open_invoices = [
        inv for inv in invoices
        if inv.status in (Invoice.Status.PENDING, Invoice.Status.IN_AUCTION)
    ]
    if not open_invoices:
        return Response(
            {"detail": "This publication has no open invoices left to fund."},
            status=status.HTTP_409_CONFLICT,
        )

    lender_id = request.data.get("lender_id")
    try:
        lender = Lender.objects.get(pk=lender_id)
    except (Lender.DoesNotExist, TypeError, ValueError):
        return Response({"detail": "Unknown lender_id."}, status=status.HTTP_400_BAD_REQUEST)

    now = timezone.now()
    accepted_offers = []
    assessments = {invoice.pk: assess_invoice(invoice) for invoice in open_invoices}
    failed_invoice = next(
        (
            invoice
            for invoice in open_invoices
            if assessments[invoice.pk].decision != RiskAssessment.Decision.APPROVE
        ),
        None,
    )
    if failed_invoice is not None:
        return Response(
            {
                "detail": "One or more invoices did not pass automatic underwriting.",
                "invoice_id": failed_invoice.pk,
                "assessment": RiskAssessmentSerializer(
                    assessments[failed_invoice.pk]
                ).data,
            },
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    with transaction.atomic():
        for invoice in open_invoices:
            assessment = assessments[invoice.pk]
            quote = next(
                (
                    q
                    for q in rank_offers(invoice, assessment)
                    if q["lender"]["id"] == lender.pk
                ),
                None,
            )
            if quote is None:
                continue
            rate = Decimal(str(quote["rate"]))
            financing_cost = Decimal(str(quote["financing_cost"]))

            offer = Offer.objects.filter(invoice=invoice, lender=lender).order_by("pk").first()
            if offer is None:
                offer = Offer(invoice=invoice, lender=lender)
            offer.advance_percentage = Decimal(str(quote["advance_percentage"]))
            offer.rate = rate
            offer.risk_assessment = assessment
            offer.net_amount = Decimal(str(quote["net_amount"]))
            offer.financing_cost = financing_cost
            offer.funding_time = FUNDING_TIMES[lender.risk_profile]
            offer.category = "best"
            offer.rank = 1
            offer.expires_at = now + timedelta(hours=24)
            offer.is_accepted = True
            offer.accepted_at = now
            offer.save()
            accepted_offers.append(offer)

            invoice.status = Invoice.Status.FUNDED
            invoice.save(update_fields=["status"])

    total_net_amount = sum((offer.net_amount for offer in accepted_offers), Decimal("0"))

    return Response(
        {
            "batch_id": batch.id,
            "lender_id": lender.pk,
            "status": "accepted",
            "invoices_funded": len(accepted_offers),
            "total_net_amount": str(total_net_amount),
            "transaction_id": f"TXN-{uuid4().hex[:12].upper()}",
            "accepted_at": now.isoformat(),
        }
    )


@api_view(["GET"])
def financier_portfolio(request):
    """
    The demo Financiadora's own portfolio, derived entirely from real
    persisted Offers: capital on hand (Lender.available_capital), capital
    currently deployed, realized return, active operations, a risk
    breakdown, a trailing 6-month capital history, and recent operations.
    See API_CONTRACT.md.
    """
    lender = Lender.objects.order_by("id").first()
    if lender is None:
        return Response({"detail": "No lender configured."}, status=status.HTTP_404_NOT_FOUND)

    accepted = list(
        Offer.objects.filter(lender=lender, is_accepted=True)
        .select_related("invoice", "invoice__debtor_client")
        .order_by("-accepted_at")
    )

    financed_capital = Decimal("0")
    generated_return = Decimal("0")
    active_operations = 0
    risk_totals = {"low": Decimal("0"), "medium": Decimal("0"), "high": Decimal("0")}
    recent_operations = []

    for offer in accepted:
        invoice = offer.invoice
        if invoice.status == Invoice.Status.FUNDED:
            financed_capital += offer.net_amount
            active_operations += 1
        elif invoice.status == Invoice.Status.PAID:
            generated_return += offer.financing_cost

        risk = opportunity_summary(invoice)["risk"]
        risk_totals[risk] += offer.net_amount

        recent_operations.append(
            {
                "invoice_folio": f"FAC-2026-{invoice.id:04d}",
                "debtor": invoice.debtor_client.name,
                "capital": str(offer.net_amount),
                "term_days": (invoice.due_date - invoice.issue_date).days,
                "status": invoice.status,
                "return": str(offer.financing_cost),
            }
        )

    today = timezone.now().date()
    months = []
    cursor = today.replace(day=1)
    for _ in range(6):
        months.append(cursor)
        cursor = (cursor - timedelta(days=1)).replace(day=1)
    months.reverse()

    capital_history = []
    for month_start in months:
        next_month = (month_start + timedelta(days=32)).replace(day=1)
        month_total = sum(
            (
                offer.net_amount
                for offer in accepted
                if offer.accepted_at and month_start <= offer.accepted_at.date() < next_month
            ),
            Decimal("0"),
        )
        capital_history.append({"month": month_start.strftime("%Y-%m"), "amount": str(month_total)})

    return Response(
        {
            "available_capital": str(lender.available_capital),
            "financed_capital": str(financed_capital),
            "generated_return": str(generated_return),
            "active_operations_count": active_operations,
            "portfolio_by_risk": {key: str(value) for key, value in risk_totals.items()},
            "capital_history": capital_history,
            "recent_operations": recent_operations[:10],
        }
    )


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
