from django.db import models

from empresas.models import Company, DebtorClient


class InvoiceBatch(models.Model):
    """
    A set of a Company's invoices published together, as one package, to
    seek financing — a financiadora bidding on the batch funds all of its
    invoices at once and collects the yield across all of them.
    """

    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="invoice_batches"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Batch #{self.pk} — {self.company}"


class Invoice(models.Model):
    """A receivable submitted by a Company against one of its DebtorClients."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_AUCTION = "in_auction", "In auction"
        FUNDED = "funded", "Funded"
        PAID = "paid", "Paid"
        OVERDUE = "overdue", "Overdue"

    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="invoices"
    )
    debtor_client = models.ForeignKey(
        DebtorClient, on_delete=models.CASCADE, related_name="invoices"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    issue_date = models.DateField()
    due_date = models.DateField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    # Set when this invoice has been published as part of a multi-invoice
    # batch (see InvoiceBatch). Null means it's either unpublished or was
    # published individually via the single-invoice offers flow.
    batch = models.ForeignKey(
        InvoiceBatch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoices",
    )

    def __str__(self):
        return f"Invoice #{self.pk} — {self.company} ({self.amount})"
