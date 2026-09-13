from decimal import Decimal

from django.db.models import Count, Prefetch, Q
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.risk_engine import assess_invoice
from empresas.models import Company

from . import assistant
from .models import Invoice, InvoiceBatch
from .package_optimizer import recommend_package
from .serializers import InvoiceBatchSerializer, InvoiceSerializer, RiskAssessmentSerializer
from .services import build_liquidity_candidates, publish_invoices


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


@api_view(["POST"])
def invoice_assistant(request):
    """
    Chat turn with the Gemini-powered assistant that recommends which
    available invoices to bundle into a publication. Body: {"message": str,
    "history": [{"role": "user"|"model", "text": str}, ...]}. See
    facturas/assistant.py and API_CONTRACT.md.
    """
    message = (request.data.get("message") or "").strip()
    if not message:
        return Response({"detail": "message is required."}, status=status.HTTP_400_BAD_REQUEST)

    company = Company.objects.order_by("id").first()
    if company is None:
        return Response({"detail": "No company configured."}, status=status.HTTP_404_NOT_FOUND)

    try:
        result = assistant.chat(company, message, request.data.get("history"))
    except RuntimeError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception:
        return Response(
            {"detail": "El asistente no está disponible en este momento."},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    return Response(
        {"reply": result["reply"], "published_batch_id": result["published_batch_id"]}
    )


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
    POST publishes one or more of the empresa's own available invoices
    together as one "publicación" (a package a financiadora can browse
    and fund as a whole — a single invoice is just a publication of
    size 1). GET lists every publication published so far.
    See API_CONTRACT.md.
    """
    if request.method == "GET":
        batches = _batch_queryset().order_by("-created_at")
        return Response(InvoiceBatchSerializer(batches, many=True).data)

    term_days = request.data.get("term_days", 30)
    batch, error = publish_invoices(
        request.data.get("invoice_ids") or [], term_days=term_days
    )
    if error:
        return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)

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
    candidates = build_liquidity_candidates(term_days)
    recommendation = recommend_package(candidates, target) if mode == "liquidity_target" else None
    return Response({"term_days": term_days, "candidates": [{key: str(value) if isinstance(value, Decimal) else value for key, value in candidate.items()} for candidate in candidates], "recommendation": {key: str(value) if isinstance(value, Decimal) else value for key, value in recommendation.items()} if recommendation else None})


@api_view(["GET"])
def invoice_batch_detail(request, batch_id):
    try:
        batch = _batch_queryset().get(pk=batch_id)
    except InvoiceBatch.DoesNotExist:
        return Response({"detail": "Batch not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response(InvoiceBatchSerializer(batch).data)
