"""
Lender pricing agents: given a predicted {p10, p50, p90} days-late risk
band and an invoice amount, each agent decides how much of the invoice
to advance (advance_percentage) and at what discount rate (rate).

Each agent solves a small convex program (via cvxpy) to pick the advance
percentage x: maximize the rate earned on the funded amount minus a
quadratic penalty on risk exposure, subject to the agent's own bounds on
x. The rate itself comes from a per-agent policy formula driven by the
risk band, then is held fixed while cvxpy solves for x — keeping the
objective a proper concave QP (rate * x would be bilinear/non-convex if
both were free variables solved jointly).

Demo-scale, not calibrated underwriting: the formulas encode the
*qualitative* behavior asked for (conservative pulls back hard on high
p90, aggressive stays looser but caps absolute loan size, specialized
only sharpens pricing inside its configured sectors) rather than
real-world-tuned coefficients.
"""

from dataclasses import dataclass

import cvxpy as cp

NORMAL_TERM_DAYS = 30.0


def _risk_scores(risk):
    """Two derived, dimensionless risk signals from the p10/p50/p90 band."""
    tail_risk = risk["p90"] / NORMAL_TERM_DAYS
    uncertainty = (risk["p90"] - risk["p10"]) / NORMAL_TERM_DAYS
    return tail_risk, uncertainty


def _solve_advance_percentage(rate, risk_aversion, tail_risk, x_min, x_max):
    """
    Concave QP, in the advance *fraction* x (not dollars funded):
        maximize   rate * x - risk_aversion * tail_risk * x^2
        subject to x_min <= x <= x_max

    Penalizing x rather than (x * amount) is deliberate: risk exposure as
    a *fraction* of the invoice is what the agent's risk tolerance should
    react to, independent of the invoice's absolute size. Absolute size
    only matters via the aggressive agent's max_loan_amount, which is
    handled separately by narrowing x_max before this is ever called —
    squaring the dollar amount here would make the penalty scale
    quadratically with amount and swamp the linear rate term at any real
    invoice size, collapsing every agent to x_min regardless of risk.
    """
    x = cp.Variable()
    objective = cp.Maximize(rate * x - risk_aversion * tail_risk * cp.square(x))
    problem = cp.Problem(objective, [x >= x_min, x <= x_max])
    problem.solve(solver=cp.OSQP, verbose=False, polish=False)

    if x.value is None:
        # Solver failed to converge — fall back to the agent's safe floor
        # rather than raising mid-pricing-pipeline.
        return x_min
    return float(min(max(x.value, x_min), x_max))


@dataclass
class PricingAgent:
    name: str
    risk_aversion: float
    base_rate: float
    rate_per_tail_risk: float
    rate_per_uncertainty: float
    rate_bounds: tuple
    x_bounds: tuple
    max_loan_amount: float | None = None

    def _rate(self, tail_risk, uncertainty):
        rate = (
            self.base_rate
            + self.rate_per_tail_risk * tail_risk
            + self.rate_per_uncertainty * uncertainty
        )
        lo, hi = self.rate_bounds
        return min(max(rate, lo), hi)

    def _bounds_for_amount(self, amount):
        x_min, x_max = self.x_bounds
        if self.max_loan_amount is not None:
            x_max = min(x_max, self.max_loan_amount / amount)
        x_min = min(x_min, x_max)  # keep bounds feasible if the cap bites hard
        return x_min, x_max

    def price(self, risk, amount, sector=None):
        tail_risk, uncertainty = _risk_scores(risk)
        rate = self._rate(tail_risk, uncertainty)
        x_min, x_max = self._bounds_for_amount(amount)
        x = _solve_advance_percentage(rate, self.risk_aversion, tail_risk, x_min, x_max)
        return {
            "advance_percentage": f"{x * 100:.2f}",
            "rate": f"{rate * 100:.2f}",
        }


class SpecializedAgent:
    """
    Prices better (lower rate, higher advance ceiling) for invoices whose
    `sector` is in its configured list; falls back to a cautious baseline
    for everything else.
    """

    name = "specialized"

    def __init__(self, sectors):
        self.sectors = set(sectors)
        self._in_sector = PricingAgent(
            name="specialized-in-sector",
            risk_aversion=0.0115,
            base_rate=0.008,
            rate_per_tail_risk=0.012,
            rate_per_uncertainty=0.005,
            rate_bounds=(0.008, 0.04),
            x_bounds=(0.65, 0.90),
        )
        self._out_of_sector = PricingAgent(
            name="specialized-out-of-sector",
            risk_aversion=0.0317,
            base_rate=0.018,
            rate_per_tail_risk=0.022,
            rate_per_uncertainty=0.009,
            rate_bounds=(0.018, 0.065),
            x_bounds=(0.50, 0.65),
        )

    def price(self, risk, amount, sector=None):
        profile = self._in_sector if sector in self.sectors else self._out_of_sector
        return profile.price(risk, amount, sector=sector)


def conservative_agent():
    """Tight risk tolerance — pricing reacts sharply to a high p90."""
    return PricingAgent(
        name="conservative",
        risk_aversion=0.021,
        base_rate=0.010,
        rate_per_tail_risk=0.020,
        rate_per_uncertainty=0.008,
        rate_bounds=(0.010, 0.07),
        x_bounds=(0.50, 0.75),
    )


def aggressive_agent(max_loan_amount=200_000.0):
    """Looser risk tolerance, higher advance ceiling, capped loan amount."""
    return PricingAgent(
        name="aggressive",
        risk_aversion=0.014,
        base_rate=0.015,
        rate_per_tail_risk=0.012,
        rate_per_uncertainty=0.006,
        rate_bounds=(0.015, 0.05),
        x_bounds=(0.70, 0.95),
        max_loan_amount=max_loan_amount,
    )


def specialized_agent(sectors):
    """Better pricing only for invoices whose sector is in `sectors`."""
    return SpecializedAgent(sectors)
