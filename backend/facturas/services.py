"""
Business logic shared between the REST endpoints and the assistant's
tools, so rules can't drift out of sync between them.
"""

from core.risk_engine import evaluate_invoice

from .models import Invoice, InvoiceBatch


def build_liquidity_candidates(term_days, company=None):
    """
    Every available, unbatched invoice that would be APPROVEd for factoring
    at the given hypothetical term, with its net disbursement and expected
    loss at that term — the same candidate pool package_optimizer.recommend_package
    picks from. Shared by invoice_batch_preview and the assistant's
    liquidity-target tool.
    """
    queryset = Invoice.objects.filter(
        status=Invoice.Status.AVAILABLE, batch__isnull=True
    ).select_related("company", "debtor_client")
    if company is not None:
        queryset = queryset.filter(company=company)

    candidates = []
    for invoice in queryset:
        assessment = evaluate_invoice(invoice, term_days=term_days)
        if assessment["decision"] == "APPROVE":
            candidates.append(
                {
                    "id": invoice.id,
                    "folio": f"FAC-2026-{invoice.id:04d}",
                    "amount": invoice.amount,
                    "net_disbursement": assessment["net_disbursement"],
                    "expected_loss": assessment["expected_loss"],
                }
            )
    return candidates


def publish_invoices(invoice_ids, company=None, term_days=30):
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
    if term_days not in (30, 60, 90):
        return None, "term_days must be 30, 60, or 90."

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

    batch = InvoiceBatch.objects.create(
        company_id=company_ids.pop(), factoring_term_days=term_days
    )
    Invoice.objects.filter(pk__in=invoice_ids).update(
        batch=batch, status=Invoice.Status.IN_AUCTION
    )
    return batch, None
