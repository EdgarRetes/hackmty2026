from datetime import date

from django.db import models


class Company(models.Model):
    """A Mexican SME requesting factoring/financing against its invoices."""

    rfc = models.CharField(max_length=13, unique=True)
    legal_name = models.CharField(max_length=255)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.legal_name


class DebtorClient(models.Model):
    """A client of a Company that owes money on invoices issued to it."""

    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="debtor_clients"
    )
    name = models.CharField(max_length=255)
    archetype = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class PaymentHistory(models.Model):
    """A past payment record for a DebtorClient, used to assess its risk."""

    debtor_client = models.ForeignKey(
        DebtorClient, on_delete=models.CASCADE, related_name="payment_history"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    days_late = models.IntegerField(default=0)
    # When this payment actually happened. Needed for recency-based risk
    # features (e.g. "days since this client's last payment") — without a
    # date, PaymentHistory records have no order in time.
    paid_at = models.DateField(default=date.today)

    class Meta:
        ordering = ["paid_at"]

    def __str__(self):
        return f"{self.debtor_client} — {self.amount} ({self.days_late}d late)"
