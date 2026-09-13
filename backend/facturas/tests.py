from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from empresas.models import Company, DebtorClient, PaymentHistory

from .models import Invoice


class InvoiceApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        company = Company.objects.create(rfc="TST010101AA1", legal_name="Empresa Real")
        debtor = DebtorClient.objects.create(company=company, name="Cliente Real", archetype="reliable")
        self.invoice = Invoice.objects.create(company=company, debtor_client=debtor, amount=Decimal("250000.00"), issue_date=date.today(), due_date=date.today() + timedelta(days=30))

    def test_lists_pending_invoices(self):
        response = self.client.get("/api/invoices/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["folio"], f"FAC-2026-{self.invoice.id:04d}")
        self.assertEqual(response.data[0]["amount"], "250000.00")
        self.assertEqual(response.data[0]["offers_count"], 0)

    def test_list_includes_non_pending_invoices(self):
        self.invoice.status = Invoice.Status.FUNDED
        self.invoice.save(update_fields=["status"])
        response = self.client.get("/api/invoices/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["status"], "funded")

    def test_retrieves_invoice_by_supported_references(self):
        references = [str(self.invoice.id), f"INV-{self.invoice.id}", f"FAC-2026-{self.invoice.id:04d}"]
        for reference in references:
            with self.subTest(reference=reference):
                response = self.client.get(f"/api/invoices/{reference}/")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data["id"], self.invoice.id)

    def test_unknown_invoice_returns_json_404(self):
        response = self.client.get("/api/invoices/INV-9999/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, {"detail": "Invoice not found."})


class InvoiceValidationTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            rfc="VAL010101AA1", legal_name="Empresa validación"
        )
        self.debtor = DebtorClient.objects.create(
            company=self.company, name="Pagador validación", archetype="reliable"
        )

    def test_rejects_due_date_before_issue_date(self):
        invoice = Invoice(
            company=self.company,
            debtor_client=self.debtor,
            amount=Decimal("1000.00"),
            outstanding_balance=Decimal("1000.00"),
            issue_date=date.today(),
            due_date=date.today() - timedelta(days=1),
        )

        with self.assertRaises(ValidationError):
            invoice.full_clean()

    def test_rejects_non_positive_outstanding_balance(self):
        invoice = Invoice(
            company=self.company,
            debtor_client=self.debtor,
            amount=Decimal("1000.00"),
            outstanding_balance=Decimal("0.00"),
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
        )

        with self.assertRaises(ValidationError):
            invoice.full_clean()


class RiskAssessmentApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        company = Company.objects.create(
            rfc="API010101AA1",
            legal_name="Empresa API",
            is_verified=True,
            annual_revenue=Decimal("10000000.00"),
            dilution_rate=Decimal("0.01000"),
        )
        debtor = DebtorClient.objects.create(
            company=company,
            name="Pagador API",
            archetype="reliable",
            rfc="PAG010101AA1",
            bureau_score=730,
            current_ratio=Decimal("1.90"),
            debt_to_ebitda=Decimal("1.80"),
            operating_margin=Decimal("0.13000"),
        )
        for index in range(6):
            due_at = date.today() - timedelta(days=240 - index * 30)
            PaymentHistory.objects.create(
                debtor_client=debtor,
                amount=Decimal("100000.00"),
                amount_paid=Decimal("100000.00"),
                issued_at=due_at - timedelta(days=30),
                due_at=due_at,
                paid_at=due_at,
            )
        self.invoice = Invoice.objects.create(
            company=company,
            debtor_client=debtor,
            amount=Decimal("150000.00"),
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=45),
            cfdi_uuid="22222222-2222-4222-8222-222222222222",
            issuer_rfc=company.rfc,
            receiver_rfc=debtor.rfc,
            xml_hash="api-invoice-hash",
        )

    def test_post_creates_and_get_returns_latest_assessment(self):
        url = f"/api/invoices/{self.invoice.id}/risk-assessment/"

        created = self.client.post(url)
        fetched = self.client.get(url)

        self.assertEqual(created.status_code, 201)
        self.assertEqual(fetched.status_code, 200)
        self.assertEqual(created.data["id"], fetched.data["id"])
        self.assertEqual(created.data["decision"], "APPROVE")
        self.assertIn(created.data["rating"], {"A", "B"})
        self.assertEqual(created.data["policy_version"], "hackathon-v1")
        self.assertEqual(created.data["reference_rate_as_of"], "2026-09-11")
        self.assertTrue(created.data["reasons"])

    def test_get_without_assessment_returns_404(self):
        response = self.client.get(
            f"/api/invoices/{self.invoice.id}/risk-assessment/"
        )

        self.assertEqual(response.status_code, 404)
