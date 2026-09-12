"""
Sanity-check for core.risk_engine: builds one in-memory (unsaved) test
invoice per demo DebtorClient — all using the SAME amount, so amount_ratio
stays ~1.0 for everyone — and prints the predicted p10/p50/p90 delay band.

The point is to eyeball whether the band's center and width move the way
they should: delinquent should sit high, reliable should be tight and
low, irregular should be wide, and new (little/no history) should be
wide too since the model has almost nothing to go on for that client.

Run from backend/:
    python scripts/test_risk_engine.py
"""

import os
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "factorai_config.settings.dev")

import django  # noqa: E402

django.setup()

from empresas.models import DebtorClient  # noqa: E402
from facturas.models import Invoice  # noqa: E402

from core.risk_engine import predict_risk  # noqa: E402

TEST_AMOUNT = Decimal("100000.00")


def main():
    clients = list(
        DebtorClient.objects.select_related("company").order_by("archetype", "name")
    )
    if not clients:
        print("No DebtorClients found — run `python manage.py seed_demo_data` first.")
        return

    today = date.today()
    header = f"{'Client':<32}{'Archetype':<12}{'p10':>6}{'p50':>6}{'p90':>6}{'width':>8}"
    print(header)
    print("-" * len(header))

    for client in clients:
        # Unsaved on purpose — just a vehicle to feed a consistent test
        # amount through predict_risk() without touching the database.
        invoice = Invoice(
            company=client.company,
            debtor_client=client,
            amount=TEST_AMOUNT,
            issue_date=today,
            due_date=today,
            status=Invoice.Status.PENDING,
        )
        band = predict_risk(invoice)
        width = band["p90"] - band["p10"]
        print(
            f"{client.name:<32}{client.archetype:<12}"
            f"{band['p10']:>6}{band['p50']:>6}{band['p90']:>6}{width:>8}"
        )


if __name__ == "__main__":
    main()
