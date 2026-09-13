from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase

from empresas.models import Company, DebtorClient, PaymentHistory
from facturas.models import Invoice, RiskAssessment

from .risk_engine import assess_invoice, evaluate_invoice, predict_risk


AS_OF = date(2026, 9, 12)


class RiskEngineTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            rfc="EMI850101AB1",
            legal_name="Emisora Demo",
            is_verified=True,
            scian_sector="333",
            years_operating=12,
            annual_revenue=Decimal("12000000.00"),
            dispute_rate=Decimal("0.01000"),
            dilution_rate=Decimal("0.01000"),
        )

    def make_debtor(self, suffix="1", **overrides):
        values = {
            "company": self.company,
            "name": f"Pagador {suffix}",
            "archetype": "reliable",
            "rfc": f"PAG850101A{suffix}1",
            "scian_sector": "461",
            "employee_band": "51-100",
            "years_operating": 10,
            "bureau_score": 720,
            "current_ratio": Decimal("1.80"),
            "debt_to_ebitda": Decimal("2.00"),
            "operating_margin": Decimal("0.12000"),
        }
        values.update(overrides)
        return DebtorClient.objects.create(**values)

    def add_history(self, debtor, dpd_values, defaults=None):
        defaults = defaults or set()
        for index, dpd in enumerate(dpd_values):
            issued = AS_OF - timedelta(days=300 - index * 40)
            due = issued + timedelta(days=30)
            PaymentHistory.objects.create(
                debtor_client=debtor,
                amount=Decimal("100000.00"),
                amount_paid=Decimal("100000.00") if index not in defaults else Decimal("0.00"),
                issued_at=issued,
                due_at=due,
                paid_at=due + timedelta(days=dpd),
                is_default=index in defaults,
            )

    def make_invoice(self, debtor, term_days=45, **overrides):
        values = {
            "company": self.company,
            "debtor_client": debtor,
            "amount": Decimal("200000.00"),
            "outstanding_balance": Decimal("200000.00"),
            "issue_date": AS_OF - timedelta(days=5),
            "due_date": AS_OF + timedelta(days=term_days),
            "cfdi_uuid": f"00000000-0000-4000-8000-{debtor.pk:012d}",
            "issuer_rfc": self.company.rfc,
            "receiver_rfc": debtor.rfc,
            "payment_method": "PPD",
            "sat_status": "vigente",
            "xml_hash": f"hash-{debtor.pk}",
            "has_delivery_evidence": True,
        }
        values.update(overrides)
        return Invoice.objects.create(**values)

    def test_approves_valid_invoice_and_calculates_expected_loss(self):
        debtor = self.make_debtor()
        self.add_history(debtor, [0, 0, 2, 0, 1, 0])
        invoice = self.make_invoice(debtor)

        result = evaluate_invoice(invoice, as_of=AS_OF)

        self.assertEqual(result["decision"], "APPROVE")
        self.assertIn(result["rating"], {"A", "B"})
        expected_default = (
            result["probability_of_default"]
            * result["loss_given_default"]
            * result["exposure_at_default"]
        ).quantize(Decimal("0.01"))
        self.assertEqual(result["expected_default_loss"], expected_default)
        self.assertGreater(result["net_disbursement"], Decimal("0"))
        self.assertGreater(result["expected_investor_profit"], Decimal("0"))

    def test_rejects_cancelled_cfdi_before_scoring(self):
        debtor = self.make_debtor()
        self.add_history(debtor, [0, 0, 0, 0, 0])
        invoice = self.make_invoice(debtor, sat_status="cancelado")

        result = evaluate_invoice(invoice, as_of=AS_OF)

        self.assertEqual(result["decision"], "REJECT")
        self.assertIn("CFDI_CANCELLED", result["reason_codes"])
        self.assertEqual(result["recommended_advance_percentage"], Decimal("0"))

    def test_rejects_high_credit_risk(self):
        debtor = self.make_debtor(
            bureau_score=430,
            current_ratio=Decimal("0.60"),
            debt_to_ebitda=Decimal("7.00"),
            operating_margin=Decimal("-0.05000"),
            has_legal_events=True,
        )
        self.add_history(debtor, [60, 75, 90, 95, 110, 120], defaults={3, 4, 5})
        invoice = self.make_invoice(debtor)

        result = evaluate_invoice(invoice, as_of=AS_OF)

        self.assertEqual(result["decision"], "REJECT")
        self.assertEqual(result["rating"], "E")
        self.assertIn("CREDIT_RISK_TOO_HIGH", result["reason_codes"])

    def test_sends_new_debtor_to_manual_review(self):
        debtor = self.make_debtor(bureau_score=None)
        invoice = self.make_invoice(debtor)

        result = evaluate_invoice(invoice, as_of=AS_OF)

        self.assertEqual(result["decision"], "REVIEW")
        self.assertIn("INSUFFICIENT_PAYMENT_HISTORY", result["reason_codes"])

    def test_longer_term_increases_cost_for_same_risk(self):
        debtor = self.make_debtor()
        self.add_history(debtor, [0, 0, 2, 0, 1, 0])
        invoice_30 = self.make_invoice(debtor, term_days=30)
        invoice_90 = self.make_invoice(
            debtor,
            term_days=90,
            cfdi_uuid="00000000-0000-4000-8000-999999999999",
            xml_hash="hash-term-90",
        )

        result_30 = evaluate_invoice(invoice_30, as_of=AS_OF)
        result_90 = evaluate_invoice(invoice_90, as_of=AS_OF)

        self.assertGreater(result_90["financing_cost"], result_30["financing_cost"])

    def test_higher_risk_never_increases_advance(self):
        healthy = self.make_debtor(suffix="1")
        weak = self.make_debtor(
            suffix="2",
            bureau_score=610,
            current_ratio=Decimal("1.05"),
            debt_to_ebitda=Decimal("4.50"),
            operating_margin=Decimal("0.03000"),
        )
        self.add_history(healthy, [0, 0, 0, 1, 0, 0])
        self.add_history(weak, [10, 15, 20, 25, 30, 35])

        low_risk = evaluate_invoice(self.make_invoice(healthy), as_of=AS_OF)
        high_risk = evaluate_invoice(self.make_invoice(weak), as_of=AS_OF)

        self.assertGreater(high_risk["risk_score"], low_risk["risk_score"])
        self.assertLessEqual(
            high_risk["recommended_advance_percentage"],
            low_risk["recommended_advance_percentage"],
        )

    def test_assess_invoice_persists_reproducible_snapshot(self):
        debtor = self.make_debtor()
        self.add_history(debtor, [0, 0, 2, 0, 1, 0])
        invoice = self.make_invoice(debtor)

        assessment = assess_invoice(invoice, as_of=AS_OF)

        self.assertIsInstance(assessment, RiskAssessment)
        self.assertEqual(assessment.policy_version, "hackathon-v1")
        self.assertEqual(assessment.reference_rate_as_of, date(2026, 9, 11))
        self.assertEqual(assessment.input_snapshot["invoice"]["cfdi_uuid"], invoice.cfdi_uuid)

    def test_legacy_delay_band_uses_contractual_dpd(self):
        debtor = self.make_debtor()
        self.add_history(debtor, [0, 2, 5, 8, 10])
        invoice = self.make_invoice(debtor)

        band = predict_risk(invoice)

        self.assertEqual(band, {"p10": 0, "p50": 5, "p90": 10})
