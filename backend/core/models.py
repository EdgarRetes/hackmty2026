from django.conf import settings
from django.db import models

# TimescaleDB note for future hypertables: modern TimescaleDB (on Tiger
# Cloud) creates hypertables declaratively via
#   CREATE TABLE ... WITH (tsdb.hypertable = true, tsdb.partition_column = '...')
# NOT the legacy create_hypertable() function call. Check current Tiger
# Data docs before writing any migration that creates a hypertable, since
# this syntax has changed across TimescaleDB versions.


class UserProfile(models.Model):
    """
    Which of the platform's two roles a Django user acts as, and which
    domain entity (Company or Lender) they represent. There's no login
    flow wired up yet — the frontend role switcher just reads these via
    GET /api/profiles/ — but the identity itself is real, not hardcoded.
    """

    class Role(models.TextChoices):
        EMPRESA = "empresa", "Empresa"
        FINANCIADORA = "financiadora", "Financiadora"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    display_name = models.CharField(max_length=255)
    company = models.ForeignKey(
        "empresas.Company",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="profiles",
    )
    lender = models.ForeignKey(
        "financiadoras.Lender",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="profiles",
    )

    def __str__(self):
        return f"{self.display_name} ({self.role})"
