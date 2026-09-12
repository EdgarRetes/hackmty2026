from datetime import date

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .fixtures import DEMO_INVOICES


@api_view(["GET"])
def invoice_list(request):
    """
    TEMPORARY: returns hardcoded example invoices instead of querying the
    database. See API_CONTRACT.md.
    """
    today = date.today()
    invoices = []
    for invoice in DEMO_INVOICES:
        due_date = date.fromisoformat(invoice["due_date"])
        invoices.append({**invoice, "days_until_due": (due_date - today).days})

    return Response(invoices)
