"""
Matching engine: runs a real pending Invoice through the risk engine and
all three lender pricing agents, then ranks the resulting quotes by net
cash to the empresa — the amount actually advanced up front, since
that's what the SME can use today. Ties broken by the lower rate
(cheaper cost of capital), highest net cash first.
"""

from decimal import ROUND_HALF_UP, Decimal

from core.demo_sectors import SPECIALIZED_SECTORS, sector_for_client
from core.pricing_agents import aggressive_agent, conservative_agent, specialized_agent
from core.risk_engine import predict_risk

# One representative lender identity per pricing agent/strategy.
LENDER_IDENTITIES = {
    "conservative": {"id": 1, "name": "Financiera del Bajío", "risk_profile": "conservative"},
    "aggressive": {"id": 2, "name": "Capital Ágil MX", "risk_profile": "aggressive"},
    "specialized": {"id": 3, "name": "Fondeo Azteca", "risk_profile": "specialized"},
}


def _money(value):
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def rank_offers(invoice):
    """
    Returns a list of {"lender", "advance_percentage", "rate", "net_amount"}
    dicts — one per pricing agent — sorted by net_amount (cash advanced to
    the empresa today) descending, highest first.
    """
    risk = predict_risk(invoice)
    amount = Decimal(str(invoice.amount))
    sector = sector_for_client(invoice.debtor_client)

    agents = {
        "conservative": conservative_agent(),
        "aggressive": aggressive_agent(),
        "specialized": specialized_agent(SPECIALIZED_SECTORS),
    }

    quotes = []
    for agent_key, agent in agents.items():
        quote = agent.price(risk, float(amount), sector=sector)
        advance_percentage = Decimal(quote["advance_percentage"])
        rate = Decimal(quote["rate"])
        net_amount = amount * advance_percentage / Decimal("100")
        quotes.append(
            {
                "lender": LENDER_IDENTITIES[agent_key],
                "advance_percentage": quote["advance_percentage"],
                "rate": quote["rate"],
                "net_amount": _money(net_amount),
                "_sort_key": (-net_amount, rate),
            }
        )

    quotes.sort(key=lambda q: q["_sort_key"])
    for quote in quotes:
        del quote["_sort_key"]
    return quotes
