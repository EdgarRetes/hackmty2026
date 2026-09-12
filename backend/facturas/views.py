from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Invoice
from .serializers import InvoiceSerializer


def _invoice_queryset():
    return Invoice.objects.select_related("company", "debtor_client")


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
    Real pending invoices from the database (seeded via
    `manage.py seed_demo_data`). See API_CONTRACT.md.
    """
    invoices = _invoice_queryset().filter(status=Invoice.Status.PENDING).order_by("due_date")
    return Response(InvoiceSerializer(invoices, many=True).data)


@api_view(["GET"])
def invoice_detail(request, reference):
    invoice = _invoice_from_reference(reference)
    if invoice is None:
        return Response(
            {"detail": "Invoice not found."}, status=status.HTTP_404_NOT_FOUND
        )
    return Response(InvoiceSerializer(invoice).data)
