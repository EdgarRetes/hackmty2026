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
    is_accepted = models.BooleanField(default=False)

    def __str__(self):
        return f"Offer by {self.lender} on {self.invoice}"
