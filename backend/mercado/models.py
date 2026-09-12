from django.db import models

from facturas.models import Invoice
from financiadoras.models import Lender


class Offer(models.Model):
    """A bid placed by a Lender on an Invoice."""

    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name="offers"
    )
    lender = models.ForeignKey(
        Lender, on_delete=models.CASCADE, related_name="offers"
    )
    advance_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    rate = models.DecimalField(max_digits=5, decimal_places=2)
    net_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    financing_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    funding_time = models.CharField(max_length=50, default="24 horas")
    category = models.CharField(max_length=50, blank=True)
    rank = models.PositiveSmallIntegerField(default=0)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_accepted = models.BooleanField(default=False)
    accepted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["rank", "rate"]

    def __str__(self):
        return f"Offer by {self.lender} on {self.invoice}"
