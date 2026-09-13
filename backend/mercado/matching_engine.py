"""Transparent lender variants around an approved risk recommendation."""

from decimal import ROUND_HALF_UP, Decimal

from core.risk_engine import assess_invoice
from facturas.models import RiskAssessment

LENDER_IDENTITIES = {
    "conservative": {"id": 1, "name": "Financiera del Bajío", "risk_profile": "conservative"},
    "aggressive": {"id": 2, "name": "Capital Ágil MX", "risk_profile": "aggressive"},
    "specialized": {"id": 3, "name": "Fondeo Azteca", "risk_profile": "specialized"},
}


def _money(value):
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _monthly_rate(annual_rate):
    return Decimal(str((1 + float(annual_rate)) ** (1 / 12) - 1))


def _period_factor(annual_rate, days):
    return Decimal(str((1 + float(annual_rate)) ** (days / 360) - 1))


def rank_offers(invoice, assessment):
    """Return three term-priced offers; only approved assessments are accepted."""
    if assessment.decision != RiskAssessment.Decision.APPROVE:
        return []

    base_advance = Decimal(assessment.recommended_advance_percentage)
    base_rate = Decimal(assessment.recommended_annual_rate)
    is_specialized = invoice.debtor_client.scian_sector.startswith(("31", "32", "33"))
    profiles = {
        "conservative": (max(Decimal("50"), base_advance - Decimal("10")), max(assessment.reference_rate, base_rate - Decimal("0.005"))),
        "aggressive": (min(Decimal("95"), base_advance + Decimal("5")), base_rate + Decimal("0.015")),
        "specialized": (
            min(Decimal("92"), base_advance + (Decimal("2") if is_specialized else Decimal("-5"))),
            max(assessment.reference_rate, base_rate + (Decimal("-0.005") if is_specialized else Decimal("0.010"))),
        ),
    }
    amount = Decimal(invoice.outstanding_balance or invoice.amount)
    quotes = []
    for key, (advance_percentage, annual_rate) in profiles.items():
        gross_advance = _money(amount * advance_percentage / Decimal("100"))
        financing_cost = _money(gross_advance * _period_factor(annual_rate, assessment.term_days))
        cash_after_cost = _money(gross_advance - financing_cost)
        quotes.append(
            {
                "lender": LENDER_IDENTITIES[key],
                "advance_percentage": f"{advance_percentage:.2f}",
                "rate": f"{_monthly_rate(annual_rate) * Decimal('100'):.2f}",
                "annual_rate": annual_rate,
                "net_amount": f"{cash_after_cost:.2f}",
                "financing_cost": f"{financing_cost:.2f}",
                "_sort_key": (-cash_after_cost, annual_rate),
            }
        )
    quotes.sort(key=lambda quote: quote["_sort_key"])
    for quote in quotes:
        del quote["_sort_key"]
    return quotes


def _risk_bucket(risk_score):
    """Coarse low/medium/high bucket for marketplace/portfolio display."""
    if risk_score <= 30:
        return "low"
    if risk_score <= 60:
        return "medium"
    return "high"


def opportunity_summary(invoice):
    """
    A lightweight summary for marketplace-list and portfolio views: the
    risk bucket the invoice's DebtorClient falls into, plus an estimated
    return (rate and absolute amount) averaged across all 3 pricing
    agents — a rough "what any lender could expect" figure, not tied to
    one specific agent's strategy.
    """
    assessment = invoice.risk_assessments.order_by("-created_at").first()
    if assessment is None:
        assessment = assess_invoice(invoice)
    quotes = rank_offers(invoice, assessment)
    amount = Decimal(str(invoice.amount))

    avg_rate = (
        sum(Decimal(quote["rate"]) for quote in quotes) / len(quotes)
        if quotes
        else Decimal("0")
    )
    avg_rate = avg_rate.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    estimated_return = (amount * avg_rate / Decimal("100")).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    return {
        "risk": _risk_bucket(assessment.risk_score),
        "estimated_return_rate": str(avg_rate),
        "estimated_return": str(estimated_return),
        "sector": invoice.debtor_client.scian_sector or None,
    }
