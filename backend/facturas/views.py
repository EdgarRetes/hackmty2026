from django.db.models import Count, Prefetch, Q
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Invoice, InvoiceBatch
from .serializers import InvoiceBatchSerializer, InvoiceSerializer


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

    batch = InvoiceBatch.objects.create(company_id=company_ids.pop())
    Invoice.objects.filter(pk__in=invoice_ids).update(
        batch=batch, status=Invoice.Status.IN_AUCTION
    )

    return Response(
        InvoiceBatchSerializer(_batch_queryset().get(pk=batch.pk)).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
def invoice_batch_detail(request, batch_id):
    try:
        batch = _batch_queryset().get(pk=batch_id)
    except InvoiceBatch.DoesNotExist:
        return Response({"detail": "Batch not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response(InvoiceBatchSerializer(batch).data)
