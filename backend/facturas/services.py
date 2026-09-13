"""
Business logic shared between the REST endpoint and the assistant's
publish tool, so publishing rules can't drift out of sync between them.
"""

from .models import Invoice, InvoiceBatch


def publish_invoices(invoice_ids, company=None):
    """
    Bundle one or more of a company's own available, unbatched invoices
    into a new InvoiceBatch ("publicación"). Returns (batch, None) on
    success or (None, error_message) if the input is invalid — never
    raises for a bad `invoice_ids` list, so callers can surface the
    message directly to a user or an LLM tool result.

    `company`, when given, additionally restricts the lookup to that
    company's own invoices (used by the assistant, which must never let
    the model touch another company's data).
    """
    if not isinstance(invoice_ids, list) or len(invoice_ids) < 1:
        return None, "invoice_ids must be a list of at least 1 invoice id."

    queryset = Invoice.objects.filter(
        pk__in=invoice_ids, status=Invoice.Status.AVAILABLE, batch__isnull=True
    )
    if company is not None:
        queryset = queryset.filter(company=company)
    invoices = list(queryset)

    if len(invoices) != len(set(invoice_ids)):
        return None, (
            "One or more invoice_ids don't exist, aren't available, "
            "or are already part of another batch."
        )

    company_ids = {invoice.company_id for invoice in invoices}
    if len(company_ids) != 1:
        return None, "All invoices in a batch must belong to the same company."

    batch = InvoiceBatch.objects.create(company_id=company_ids.pop())
    Invoice.objects.filter(pk__in=invoice_ids).update(
        batch=batch, status=Invoice.Status.IN_AUCTION
    )
    return batch, None
