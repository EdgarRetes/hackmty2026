from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q

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
        AVAILABLE = "available", "Available"
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
    outstanding_balance = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    issue_date = models.DateField()
    due_date = models.DateField()
    cfdi_uuid = models.CharField(max_length=36, blank=True, default="")
    issuer_rfc = models.CharField(max_length=13, blank=True, default="")
    receiver_rfc = models.CharField(max_length=13, blank=True, default="")
    currency = models.CharField(max_length=3, default="MXN")
    payment_method = models.CharField(max_length=3, default="PPD")
    sat_status = models.CharField(max_length=20, default="vigente")
    sat_verified_at = models.DateTimeField(null=True, blank=True)
    xml_hash = models.CharField(max_length=64, blank=True, default="")
    is_disputed = models.BooleanField(default=False)
    has_delivery_evidence = models.BooleanField(default=True)
    is_previously_assigned = models.BooleanField(default=False)
    demo_scenario = models.CharField(max_length=40, blank=True, default="")
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

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0), name="invoice_amount_positive"
            ),
            models.CheckConstraint(
                condition=Q(outstanding_balance__isnull=True)
                | Q(outstanding_balance__gt=0),
                name="invoice_outstanding_balance_positive",
            ),
            models.CheckConstraint(
                condition=Q(due_date__gte=F("issue_date")),
                name="invoice_due_on_or_after_issue",
            ),
        ]

    def clean(self):
        errors = {}
        balance = self.outstanding_balance
        if balance is None:
            balance = self.amount
        if balance is None or balance <= Decimal("0"):
            errors["outstanding_balance"] = "Outstanding balance must be positive."
        if self.issue_date and self.due_date and self.due_date < self.issue_date:
            errors["due_date"] = "Due date cannot be before issue date."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.outstanding_balance is None:
            self.outstanding_balance = self.amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Invoice #{self.pk} — {self.company} ({self.amount})"


class RiskAssessment(models.Model):
    class Decision(models.TextChoices):
        APPROVE = "APPROVE", "Approve"
        REVIEW = "REVIEW", "Manual review"
        REJECT = "REJECT", "Reject"

    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name="risk_assessments"
    )
    decision = models.CharField(max_length=10, choices=Decision.choices)
    rating = models.CharField(max_length=1)
    risk_score = models.DecimalField(max_digits=5, decimal_places=2)
    probability_of_default = models.DecimalField(max_digits=7, decimal_places=6)
    loss_given_default = models.DecimalField(max_digits=7, decimal_places=6)
    exposure_at_default = models.DecimalField(max_digits=14, decimal_places=2)
    expected_default_loss = models.DecimalField(max_digits=14, decimal_places=2)
    expected_dilution_loss = models.DecimalField(max_digits=14, decimal_places=2)
    expected_loss = models.DecimalField(max_digits=14, decimal_places=2)
    confidence = models.CharField(max_length=20)
    term_days = models.PositiveIntegerField(default=0)
    reference_rate = models.DecimalField(max_digits=8, decimal_places=7)
    reference_rate_as_of = models.DateField()
    reference_rate_source = models.URLField()
    recommended_annual_rate = models.DecimalField(max_digits=8, decimal_places=7)
    recommended_monthly_rate = models.DecimalField(max_digits=8, decimal_places=7)
    recommended_advance_percentage = models.DecimalField(
        max_digits=6, decimal_places=3
    )
    financing_cost = models.DecimalField(max_digits=14, decimal_places=2)
    net_disbursement = models.DecimalField(max_digits=14, decimal_places=2)
    expected_investor_profit = models.DecimalField(max_digits=14, decimal_places=2)
    reasons = models.JSONField(default=list)
    warnings = models.JSONField(default=list)
    input_snapshot = models.JSONField(default=dict)
    policy_version = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.invoice} — {self.rating}/{self.decision}"
