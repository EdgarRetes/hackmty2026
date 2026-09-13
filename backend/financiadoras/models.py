from django.db import models


class Lender(models.Model):
    """A financiadora that competes by placing bids on pending invoices."""

    name = models.CharField(max_length=255)
    risk_profile = models.CharField(max_length=50)
    is_verified = models.BooleanField(default=False)
    # Capital this lender has on hand to deploy — not derivable from
    # Offer/Invoice data (those only show what's already been funded),
    # so it needs to be its own field. Drives the marketplace/dashboard's
    # "Disponible para financiar" figure.
    available_capital = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    # Nessie sandbox identity (see NESSIE_EXPLORATION.md) — populated by
    # `seed_demo_data --with-nessie`. Blank until then.
    nessie_customer_id = models.CharField(max_length=64, blank=True, default="")
    nessie_account_id = models.CharField(max_length=64, blank=True, default="")

    def __str__(self):
        return self.name
