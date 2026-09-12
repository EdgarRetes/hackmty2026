from datetime import date

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Invoice


@api_view(["GET"])
def invoice_list(request):
    """
    Real pending invoices from the database (seeded via
    `manage.py seed_demo_data`). See API_CONTRACT.md.
    """
    today = date.today()
    invoices = (
        Invoice.objects.select_related("company", "debtor_client")
        .filter(status=Invoice.Status.PENDING)
        .order_by("due_date")
    )

    return Response(
        [
            {
                "id": invoice.id,
                # Invoice has no folio field on the model — this is a
                # display-only label derived from the id, not stored.
                "folio": f"FAC-2026-{invoice.id:04d}",
                "company": {
                    "id": invoice.company_id,
                    "legal_name": invoice.company.legal_name,
                    "rfc": invoice.company.rfc,
                },
                "debtor_client": {
                    "id": invoice.debtor_client_id,
                    "name": invoice.debtor_client.name,
                    "archetype": invoice.debtor_client.archetype,
                },
                "amount": str(invoice.amount),
                "issue_date": invoice.issue_date.isoformat(),
                "due_date": invoice.due_date.isoformat(),
                "status": invoice.status,
                "days_until_due": (invoice.due_date - today).days,
            }
            for invoice in invoices
        ]
    )
