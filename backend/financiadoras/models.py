from django.db import models


class Lender(models.Model):
    """A financiadora that competes by placing bids on pending invoices."""

    name = models.CharField(max_length=255)
    risk_profile = models.CharField(max_length=50)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.name
