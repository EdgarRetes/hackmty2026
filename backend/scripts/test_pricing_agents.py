"""
Sanity-check for core.pricing_agents: for each demo DebtorClient, finds
their riskiest and safest real pending Invoice (by predicted p50 from
core.risk_engine), prices both through all three agents, and prints a
comparison table.

What to eyeball:
  - conservative should pull back (lower advance%, higher rate) harder
    than aggressive as an invoice gets riskier.
  - aggressive should offer a higher advance% in general, but its
    max_loan_amount cap can bite on large invoices.
  - specialized should look like a good deal (low rate, high advance%)
    for clients in its configured sectors, and cautious/worse otherwise.

Run from backend/:
    python scripts/test_pricing_agents.py
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "factorai_config.settings.dev")

import django  # noqa: E402

django.setup()

from empresas.models import DebtorClient  # noqa: E402
from facturas.models import Invoice  # noqa: E402

from core.pricing_agents import (  # noqa: E402
    aggressive_agent,
    conservative_agent,
    specialized_agent,
)
from core.risk_engine import predict_risk  # noqa: E402

# Industry sector per demo client — independent of DebtorClient.archetype
# (which encodes payment *behavior*, not industry). Only used here to
# exercise the specialized agent's sector logic.
CLIENT_SECTORS = {
    "Comercializadora del Norte": "retail_chain",
    "Ferretería La Unión": "construction_supplies",
    "Grupo Constructor Peninsular": "construction",
    "Materiales Industriales MTY": "manufacturing",
    "Farmacias San Rafael": "pharma_retail",
    "Autotransportes del Golfo": "logistics",
}
SPECIALIZED_SECTORS = {"retail_chain", "logistics"}


def main():
    agents = {
        "conservative": conservative_agent(),
        "aggressive": aggressive_agent(),
        "specialized": specialized_agent(SPECIALIZED_SECTORS),
    }

    clients = list(
        DebtorClient.objects.select_related("company").order_by("archetype", "name")
    )
    if not clients:
        print("No DebtorClients found — run `python manage.py seed_demo_data` first.")
        return

    header = (
        f"{'Client':<28}{'Case':<10}{'Amount':>12}{'p50':>6}  "
        f"{'Agent':<14}{'Advance%':>10}{'Rate%':>8}"
    )

    for client in clients:
        invoices = list(Invoice.objects.filter(debtor_client=client))
        if not invoices:
            print(f"{client.name} — no pending invoices, skipping.\n")
            continue

        scored = sorted(
            ((inv, predict_risk(inv)) for inv in invoices),
            key=lambda pair: pair[1]["p50"],
        )
        cases = [("safest", *scored[0])]
        if len(scored) > 1:
            cases.append(("riskiest", *scored[-1]))

        sector = CLIENT_SECTORS.get(client.name)

        print(header)
        print("-" * len(header))
        for label, invoice, risk in cases:
            amount = float(invoice.amount)
            for agent_name, agent in agents.items():
                result = agent.price(risk, amount, sector=sector)
                print(
                    f"{client.name:<28}{label:<10}{amount:>12,.0f}{risk['p50']:>6}  "
                    f"{agent_name:<14}{result['advance_percentage']:>10}"
                    f"{result['rate']:>8}"
                )
        print()


if __name__ == "__main__":
    main()
