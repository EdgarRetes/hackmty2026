from django.db import models

from empresas.models import Company, DebtorClient


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

    def __str__(self):
        return f"Invoice #{self.pk} — {self.company} ({self.amount})"
