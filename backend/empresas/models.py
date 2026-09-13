from datetime import date

from django.db import models


class Company(models.Model):
    """A Mexican SME requesting factoring/financing against its invoices."""

    rfc = models.CharField(max_length=13, unique=True)
    legal_name = models.CharField(max_length=255)
    is_verified = models.BooleanField(default=False)
    scian_sector = models.CharField(max_length=10, blank=True, default="")
    years_operating = models.PositiveSmallIntegerField(default=0)
    annual_revenue = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    dispute_rate = models.DecimalField(max_digits=6, decimal_places=5, default=0)
    dilution_rate = models.DecimalField(max_digits=6, decimal_places=5, default=0)
    data_source = models.CharField(max_length=100, blank=True, default="")
    source_reference = models.URLField(blank=True, default="")
    data_as_of = models.DateField(null=True, blank=True)
    # Nessie sandbox identity (see NESSIE_EXPLORATION.md) — populated by
    # `seed_demo_data --with-nessie`. Blank until then.
    nessie_customer_id = models.CharField(max_length=64, blank=True, default="")
    nessie_account_id = models.CharField(max_length=64, blank=True, default="")

    def __str__(self):
        return self.legal_name


class DebtorClient(models.Model):
    """A client of a Company that owes money on invoices issued to it."""

    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="debtor_clients"
    )
    name = models.CharField(max_length=255)
    archetype = models.CharField(max_length=100)
    rfc = models.CharField(max_length=13, blank=True, default="")
    scian_sector = models.CharField(max_length=10, blank=True, default="")
    employee_band = models.CharField(max_length=30, blank=True, default="")
    years_operating = models.PositiveSmallIntegerField(default=0)
    bureau_score = models.PositiveSmallIntegerField(null=True, blank=True)
    current_ratio = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    debt_to_ebitda = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    operating_margin = models.DecimalField(
        max_digits=6, decimal_places=5, null=True, blank=True
    )
    has_legal_events = models.BooleanField(default=False)
    data_source = models.CharField(max_length=100, blank=True, default="")
    source_reference = models.URLField(blank=True, default="")
    data_as_of = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.name


class PaymentHistory(models.Model):
    """A past payment record for a DebtorClient, used to assess its risk."""

    debtor_client = models.ForeignKey(
        DebtorClient, on_delete=models.CASCADE, related_name="payment_history"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    days_late = models.IntegerField(default=0)
    issued_at = models.DateField(null=True, blank=True)
    due_at = models.DateField(null=True, blank=True)
    # When this payment actually happened. Needed for recency-based risk
    # features (e.g. "days since this client's last payment") — without a
    # date, PaymentHistory records have no order in time.
    paid_at = models.DateField(default=date.today)
    is_default = models.BooleanField(default=False)
    # id of the Nessie deposit created to represent this payment's money
    # movement (see NESSIE_EXPLORATION.md). Blank unless seeded with
    # `--with-nessie`.
    nessie_deposit_id = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        ordering = ["paid_at"]

    def __str__(self):
        return f"{self.debtor_client} — {self.amount} ({self.days_late}d late)"

    @property
    def days_past_due(self):
        """Calendar days paid after the contractual due date, floored at zero."""
        if self.due_at and self.paid_at:
            return max(0, (self.paid_at - self.due_at).days)
        return max(0, self.days_late)
