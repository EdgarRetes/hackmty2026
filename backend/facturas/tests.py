from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from empresas.models import Company, DebtorClient

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
