"""Explainable invoice eligibility, credit score and term-sensitive pricing."""

from decimal import ROUND_HALF_UP, Decimal
from math import ceil

from django.db.models import Sum
from django.utils import timezone

from facturas.models import Invoice, RiskAssessment

from .risk_policy import (
    CAPITAL_MARGIN,
    MAX_ANNUALIZED_LOSS_SPREAD,
    OPERATING_SPREAD,
    POLICY_VERSION,
    RATING_BANDS,
    REFERENCE_RATE,
    REFERENCE_RATE_AS_OF,
    REFERENCE_RATE_SOURCE,
)

MONEY = Decimal("0.01")
RATE = Decimal("0.0000001")


def _clamp(value, low=Decimal("0"), high=Decimal("100")):
    return min(max(Decimal(str(value)), low), high)


def _money(value):
    return Decimal(value).quantize(MONEY, rounding=ROUND_HALF_UP)


def _rate(value):
    return Decimal(value).quantize(RATE, rounding=ROUND_HALF_UP)


def _eligibility_failures(invoice, as_of):
    failures = []
    balance = invoice.outstanding_balance or invoice.amount
    checks = (
        (invoice.sat_status.lower() != "vigente", "CFDI_CANCELLED", "El CFDI no está vigente ante el SAT."),
        (invoice.payment_method.upper() != "PPD", "NOT_CREDIT_INVOICE", "La factura no usa el método de pago PPD."),
        (not invoice.issuer_rfc or invoice.issuer_rfc != invoice.company.rfc, "ISSUER_RFC_MISMATCH", "El RFC emisor no coincide con el solicitante."),
        (not invoice.receiver_rfc or invoice.receiver_rfc != invoice.debtor_client.rfc, "RECEIVER_RFC_MISMATCH", "El RFC receptor no coincide con el obligado al pago."),
        (balance <= 0, "NO_OUTSTANDING_BALANCE", "La factura no tiene saldo insoluto positivo."),
        (invoice.due_date <= as_of, "INVOICE_PAST_DUE", "La factura ya alcanzó o superó su vencimiento."),
        (invoice.is_disputed, "INVOICE_DISPUTED", "La factura está disputada."),
        (invoice.is_previously_assigned, "ALREADY_ASSIGNED", "La factura ya fue cedida."),
        (not invoice.has_delivery_evidence, "NO_DELIVERY_EVIDENCE", "No existe evidencia de entrega o aceptación."),
    )
    failures.extend((code, message) for failed, code, message in checks if failed)
    if invoice.cfdi_uuid and Invoice.objects.filter(cfdi_uuid=invoice.cfdi_uuid).exclude(pk=invoice.pk).exists():
        failures.append(("DUPLICATE_CFDI", "El UUID fiscal ya está registrado en otra factura."))
    if invoice.xml_hash and Invoice.objects.filter(xml_hash=invoice.xml_hash).exclude(pk=invoice.pk).exists():
        failures.append(("DUPLICATE_XML", "El XML ya está registrado en otra factura."))
    return failures


def _payment_metrics(invoice):
    history = list(invoice.debtor_client.payment_history.all())
    if not history:
        return {"count": 0, "average_dpd": Decimal("0"), "p90_dpd": 0, "on_time_rate": Decimal("0"), "default_rate": Decimal("0")}
    dpds = sorted(item.days_past_due for item in history)
    p90 = dpds[max(0, ceil(len(dpds) * 0.9) - 1)]
    count = Decimal(len(history))
    return {
        "count": len(history),
        "average_dpd": sum((Decimal(value) for value in dpds), Decimal("0")) / count,
        "p90_dpd": p90,
        "on_time_rate": Decimal(sum(value == 0 for value in dpds)) / count,
        "default_rate": Decimal(sum(item.is_default for item in history)) / count,
    }


def _component_scores(invoice, term_days, metrics):
    payment = _clamp(
        metrics["average_dpd"] * Decimal("1.2")
        + Decimal(metrics["p90_dpd"]) * Decimal("0.4")
        + metrics["default_rate"] * Decimal("50")
        + (Decimal("1") - metrics["on_time_rate"]) * Decimal("20")
    )
    debtor = invoice.debtor_client
    bureau = _clamp((Decimal("850") - Decimal(debtor.bureau_score or 300)) / Decimal("5.5"))
    liquidity = _clamp((Decimal("1.5") - Decimal(debtor.current_ratio or 0)) * Decimal("50"))
    leverage = _clamp(Decimal(debtor.debt_to_ebitda or 8) / Decimal("6") * Decimal("100"))
    margin = _clamp((Decimal("0.15") - Decimal(debtor.operating_margin or -0.1)) * Decimal("250"))
    debtor_score = _clamp((bureau + liquidity + leverage + margin) / Decimal("4") + (Decimal("25") if debtor.has_legal_events else Decimal("0")))
    revenue = invoice.company.annual_revenue or invoice.amount
    amount_ratio_score = _clamp((invoice.amount / revenue) * Decimal("300"))
    term_score = _clamp(Decimal(term_days) / Decimal("180") * Decimal("100"))
    dilution_score = _clamp(invoice.company.dilution_rate * Decimal("1000"))
    invoice_score = _clamp((amount_ratio_score + term_score + dilution_score) / Decimal("3"))
    active = [Invoice.Status.PENDING, Invoice.Status.AVAILABLE, Invoice.Status.IN_AUCTION]
    company_total = Invoice.objects.filter(company=invoice.company, status__in=active).aggregate(total=Sum("outstanding_balance"))["total"] or invoice.outstanding_balance or invoice.amount
    debtor_total = Invoice.objects.filter(company=invoice.company, debtor_client=debtor, status__in=active).aggregate(total=Sum("outstanding_balance"))["total"] or invoice.outstanding_balance or invoice.amount
    concentration = _clamp(Decimal(debtor_total) / Decimal(company_total) * Decimal("100")) if company_total else Decimal("100")
    return {"payment": payment, "debtor": debtor_score, "invoice": invoice_score, "concentration": concentration}


def _band_for_score(score):
    for ceiling, rating, pd, advance, lgd in RATING_BANDS:
        if score <= ceiling:
            return rating, pd, advance, lgd
    return RATING_BANDS[-1][1:]


def _period_factor(annual_rate, days):
    return Decimal(str((1 + float(annual_rate)) ** (days / 360) - 1))


def _empty_result(invoice, decision, reasons, reason_codes, as_of, rating="E", score=Decimal("100")):
    return {
        "decision": decision, "rating": rating, "risk_score": Decimal(score),
        "probability_of_default": Decimal("1") if decision == "REJECT" else Decimal("0"),
        "loss_given_default": Decimal("1") if decision == "REJECT" else Decimal("0"),
        "exposure_at_default": Decimal("0"), "expected_default_loss": Decimal("0"),
        "expected_dilution_loss": Decimal("0"), "expected_loss": Decimal("0"),
        "confidence": "low", "term_days": max(0, (invoice.due_date - as_of).days),
        "reference_rate": REFERENCE_RATE, "reference_rate_as_of": REFERENCE_RATE_AS_OF,
        "reference_rate_source": REFERENCE_RATE_SOURCE, "recommended_annual_rate": Decimal("0"),
        "recommended_monthly_rate": Decimal("0"), "recommended_advance_percentage": Decimal("0"),
        "financing_cost": Decimal("0"), "net_disbursement": Decimal("0"),
        "expected_investor_profit": Decimal("0"), "reasons": reasons,
        "reason_codes": reason_codes, "warnings": [], "components": {},
    }


def evaluate_invoice(invoice, as_of=None):
    """Return a reproducible underwriting result without persisting it."""
    as_of = as_of or timezone.localdate()
    failures = _eligibility_failures(invoice, as_of)
    if failures:
        return _empty_result(invoice, RiskAssessment.Decision.REJECT, [message for _, message in failures], [code for code, _ in failures], as_of)
    metrics = _payment_metrics(invoice)
    missing_financials = any(value is None for value in (
        invoice.debtor_client.bureau_score, invoice.debtor_client.current_ratio,
        invoice.debtor_client.debt_to_ebitda, invoice.debtor_client.operating_margin,
    ))
    if metrics["count"] < 3 or missing_financials:
        codes, reasons = [], []
        if metrics["count"] < 3:
            codes.append("INSUFFICIENT_PAYMENT_HISTORY")
            reasons.append("Se requieren al menos tres pagos históricos para aprobar automáticamente.")
        if missing_financials:
            codes.append("INCOMPLETE_DEBTOR_FINANCIALS")
            reasons.append("Faltan indicadores financieros o de crédito del obligado al pago.")
        return _empty_result(invoice, RiskAssessment.Decision.REVIEW, reasons, codes, as_of, rating="N", score=Decimal("50"))
    term_days = max(1, (invoice.due_date - as_of).days)
    components = _component_scores(invoice, term_days, metrics)
    score = _clamp(components["payment"] * Decimal("0.40") + components["debtor"] * Decimal("0.25") + components["invoice"] * Decimal("0.20") + components["concentration"] * Decimal("0.15")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    rating, pd, advance, lgd = _band_for_score(score)
    if rating == "E":
        result = _empty_result(invoice, RiskAssessment.Decision.REJECT, ["La pérdida y morosidad estimadas exceden la política automática."], ["CREDIT_RISK_TOO_HIGH"], as_of, rating=rating, score=score)
        result.update({"probability_of_default": pd, "loss_given_default": lgd, "components": components})
        return result
    balance = invoice.outstanding_balance or invoice.amount
    ead = _money(balance * advance)
    default_loss = _money(pd * lgd * ead)
    dilution_loss = _money(invoice.company.dilution_rate * ead)
    expected_loss = default_loss + dilution_loss
    loss_rate = expected_loss / ead if ead else Decimal("0")
    annualized_loss = min(loss_rate * Decimal("360") / Decimal(term_days), MAX_ANNUALIZED_LOSS_SPREAD)
    annual_rate = _rate(REFERENCE_RATE + OPERATING_SPREAD + CAPITAL_MARGIN + annualized_loss)
    monthly_rate = _rate(Decimal(str((1 + float(annual_rate)) ** (1 / 12) - 1)))
    financing_cost = _money(ead * _period_factor(annual_rate, term_days))
    funding_cost = _money(ead * _period_factor(REFERENCE_RATE, term_days))
    net_disbursement = _money(ead - financing_cost)
    investor_profit = _money(financing_cost - expected_loss - funding_cost)
    reasons = [
        f"Historial: {metrics['count']} pagos, DPD promedio {metrics['average_dpd']:.1f} y p90 {metrics['p90_dpd']} días.",
        f"Fortaleza del obligado: bureau {invoice.debtor_client.bureau_score}, liquidez {invoice.debtor_client.current_ratio}x.",
        f"Exposición al obligado: {components['concentration']:.1f}% de las facturas activas del solicitante.",
    ]
    warnings = ["Concentración elevada en un solo obligado al pago."] if components["concentration"] > Decimal("40") else []
    return {
        "decision": RiskAssessment.Decision.APPROVE, "rating": rating, "risk_score": score,
        "probability_of_default": pd, "loss_given_default": lgd, "exposure_at_default": ead,
        "expected_default_loss": default_loss, "expected_dilution_loss": dilution_loss,
        "expected_loss": expected_loss, "confidence": "high" if metrics["count"] >= 6 else "medium",
        "term_days": term_days, "reference_rate": REFERENCE_RATE,
        "reference_rate_as_of": REFERENCE_RATE_AS_OF, "reference_rate_source": REFERENCE_RATE_SOURCE,
        "recommended_annual_rate": annual_rate, "recommended_monthly_rate": monthly_rate,
        "recommended_advance_percentage": advance * Decimal("100"), "financing_cost": financing_cost,
        "net_disbursement": net_disbursement, "expected_investor_profit": investor_profit,
        "reasons": reasons, "reason_codes": [], "warnings": warnings, "components": components,
    }


def _snapshot(invoice, result):
    return {
        "invoice": {"id": invoice.pk, "cfdi_uuid": invoice.cfdi_uuid, "amount": str(invoice.amount), "outstanding_balance": str(invoice.outstanding_balance or invoice.amount), "due_date": invoice.due_date.isoformat(), "sat_status": invoice.sat_status},
        "debtor": {"id": invoice.debtor_client_id, "rfc": invoice.debtor_client.rfc, "bureau_score": invoice.debtor_client.bureau_score},
        "components": {key: str(value) for key, value in result["components"].items()},
        "reason_codes": result["reason_codes"],
    }


def assess_invoice(invoice, as_of=None):
    """Evaluate and persist an immutable RiskAssessment snapshot."""
    result = evaluate_invoice(invoice, as_of=as_of)
    values = {key: value for key, value in result.items() if key not in {"reason_codes", "components"}}
    values["input_snapshot"] = _snapshot(invoice, result)
    values["policy_version"] = POLICY_VERSION
    return RiskAssessment.objects.create(invoice=invoice, **values)


def predict_risk(invoice):
    """Compatibility delay band derived directly from contractual DPD history."""
    dpds = sorted(item.days_past_due for item in invoice.debtor_client.payment_history.all())
    if not dpds:
        return {"p10": 0, "p50": 0, "p90": 0}

    def percentile(fraction):
        index = max(0, ceil(len(dpds) * fraction) - 1)
        return dpds[index]

    return {"p10": percentile(0.1), "p50": percentile(0.5), "p90": percentile(0.9)}
