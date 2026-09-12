from django.db import models


class Lender(models.Model):
    """A financiadora that competes by placing bids on pending invoices."""

    name = models.CharField(max_length=255)
    risk_profile = models.CharField(max_length=50)
    is_verified = models.BooleanField(default=False)
    # Nessie sandbox identity (see NESSIE_EXPLORATION.md) — populated by
    # `seed_demo_data --with-nessie`. Blank until then.
    nessie_customer_id = models.CharField(max_length=64, blank=True, default="")
    nessie_account_id = models.CharField(max_length=64, blank=True, default="")

    def __str__(self):
        return self.name
