from decimal import Decimal

from django.db.models import Count, Prefetch, Q
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.risk_engine import assess_invoice, evaluate_invoice

from .models import Invoice, InvoiceBatch
from .package_optimizer import recommend_package
from .serializers import InvoiceBatchSerializer, InvoiceSerializer, RiskAssessmentSerializer


def _invoice_queryset():
    return Invoice.objects.select_related("company", "debtor_client").annotate(
        offers_count=Count("offers")
    )


def _batch_queryset():
    return InvoiceBatch.objects.select_related("company").prefetch_related(
        Prefetch("invoices", queryset=_invoice_queryset())
    )


def _invoice_from_reference(reference):
    normalized = reference.upper()
    numeric_id = None
    if reference.isdigit():
        numeric_id = int(reference)
    elif normalized.startswith("INV-") and normalized[4:].isdigit():
        numeric_id = int(normalized[4:])
    elif normalized.startswith("FAC-2026-") and normalized[9:].isdigit():
        numeric_id = int(normalized[9:])

    if numeric_id is None:
        return None
    return _invoice_queryset().filter(Q(pk=numeric_id)).first()


@api_view(["GET"])
def invoice_list(request):
    """
    Real invoices from the database (seeded via
    `manage.py seed_demo_data`). See API_CONTRACT.md.
    """
    invoices = _invoice_queryset().order_by("-issue_date", "-id")
    return Response(InvoiceSerializer(invoices, many=True).data)


@api_view(["GET"])
def invoice_detail(request, reference):
    invoice = _invoice_from_reference(reference)
    if invoice is None:
        return Response(
            {"detail": "Invoice not found."}, status=status.HTTP_404_NOT_FOUND
        )
    return Response(InvoiceSerializer(invoice).data)


@api_view(["GET", "POST"])
def invoice_risk_assessment(request, invoice_id):
    try:
        invoice = Invoice.objects.select_related("company", "debtor_client").get(pk=invoice_id)
    except Invoice.DoesNotExist:
        return Response({"detail": "Invoice not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        assessment = invoice.risk_assessments.first()
        if assessment is None:
            return Response(
                {"detail": "Risk assessment not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(RiskAssessmentSerializer(assessment).data)

    assessment = assess_invoice(invoice)
    return Response(
        RiskAssessmentSerializer(assessment).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET", "POST"])
def invoice_batch_list(request):
    """
    POST publishes one or more of the empresa's own pending invoices
    together as one "publicación" (a package a financiadora can browse
    and fund as a whole — a single invoice is just a publication of
    size 1). GET lists every publication published so far.
    See API_CONTRACT.md.
    """
    if request.method == "GET":
        batches = _batch_queryset().order_by("-created_at")
        return Response(InvoiceBatchSerializer(batches, many=True).data)

    invoice_ids = request.data.get("invoice_ids") or []
    term_days = request.data.get("term_days", 30)
    if term_days not in (30, 60, 90):
        return Response({"detail": "term_days must be 30, 60, or 90."}, status=status.HTTP_400_BAD_REQUEST)
    if not isinstance(invoice_ids, list) or len(invoice_ids) < 1:
        return Response(
            {"detail": "invoice_ids must be a list of at least 1 invoice id."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    invoices = list(
        Invoice.objects.filter(
            pk__in=invoice_ids, status=Invoice.Status.PENDING, batch__isnull=True
        )
    )
    if len(invoices) != len(set(invoice_ids)):
        return Response(
            {
                "detail": "One or more invoice_ids don't exist, aren't pending, "
                "or are already part of another batch."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    company_ids = {invoice.company_id for invoice in invoices}
    if len(company_ids) != 1:
        return Response(
            {"detail": "All invoices in a batch must belong to the same company."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    batch = InvoiceBatch.objects.create(company_id=company_ids.pop(), factoring_term_days=term_days)
    Invoice.objects.filter(pk__in=invoice_ids).update(
        batch=batch, status=Invoice.Status.IN_AUCTION
    )

    return Response(
        InvoiceBatchSerializer(_batch_queryset().get(pk=batch.pk)).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
def invoice_batch_preview(request):
    term_days = request.data.get("term_days")
    mode = request.data.get("mode")
    if term_days not in (30, 60, 90):
        return Response({"detail": "term_days must be 30, 60, or 90."}, status=status.HTTP_400_BAD_REQUEST)
    if mode not in ("manual", "liquidity_target"):
        return Response({"detail": "mode must be manual or liquidity_target."}, status=status.HTTP_400_BAD_REQUEST)
    target = request.data.get("liquidity_target")
    if mode == "liquidity_target":
        try:
            target = Decimal(str(target))
            if target <= 0:
                raise ValueError
        except (ValueError, TypeError, ArithmeticError):
            return Response({"detail": "liquidity_target must be positive."}, status=status.HTTP_400_BAD_REQUEST)
    candidates = []
    for invoice in Invoice.objects.filter(status=Invoice.Status.PENDING, batch__isnull=True).select_related("company", "debtor_client"):
        assessment = evaluate_invoice(invoice, term_days=term_days)
        if assessment["decision"] == "APPROVE":
            candidates.append({"id": invoice.id, "folio": f"FAC-2026-{invoice.id:04d}", "amount": invoice.amount, "net_disbursement": assessment["net_disbursement"], "expected_loss": assessment["expected_loss"]})
    recommendation = recommend_package(candidates, target) if mode == "liquidity_target" else None
    return Response({"term_days": term_days, "candidates": [{key: str(value) if isinstance(value, Decimal) else value for key, value in candidate.items()} for candidate in candidates], "recommendation": {key: str(value) if isinstance(value, Decimal) else value for key, value in recommendation.items()} if recommendation else None})


@api_view(["GET"])
def invoice_batch_detail(request, batch_id):
    try:
        batch = _batch_queryset().get(pk=batch_id)
    except InvoiceBatch.DoesNotExist:
        return Response({"detail": "Batch not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response(InvoiceBatchSerializer(batch).data)
