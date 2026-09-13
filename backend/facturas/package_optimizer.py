"""Selection of invoice packages by net liquidity and expected loss."""

from decimal import Decimal


def recommend_package(candidates, liquidity_target):
    """Return the best 0/1 package using a compact sparse state frontier."""
    states = [{"invoice_ids": [], "net_disbursement": Decimal("0"), "expected_loss": Decimal("0"), "total_amount": Decimal("0")}]
    for candidate in candidates:
        additions = [{
            "invoice_ids": state["invoice_ids"] + [candidate["id"]],
            "net_disbursement": state["net_disbursement"] + candidate["net_disbursement"],
            "expected_loss": state["expected_loss"] + candidate["expected_loss"],
            "total_amount": state["total_amount"] + candidate["amount"],
        } for state in states]
        states.extend(additions)
    sufficient = [state for state in states if state["net_disbursement"] >= liquidity_target]
    if sufficient:
        best = min(sufficient, key=lambda state: (state["expected_loss"], state["net_disbursement"] - liquidity_target, len(state["invoice_ids"])))
        reached = True
    else:
        best = min(states, key=lambda state: (-state["net_disbursement"], state["expected_loss"], len(state["invoice_ids"])))
        reached = False
    return {**best, "target_reached": reached, "shortfall": max(Decimal("0"), liquidity_target - best["net_disbursement"]), "excess": max(Decimal("0"), best["net_disbursement"] - liquidity_target)}
