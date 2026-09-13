from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from empresas.models import Company, DebtorClient
from facturas.models import Invoice
from financiadoras.models import Lender

from .models import Offer


class OffersApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        company = Company.objects.create(rfc="TST010101AA1", legal_name="Empresa Real")
        debtor = DebtorClient.objects.create(company=company, name="Cliente Real", archetype="reliable")
        self.invoice = Invoice.objects.create(company=company, debtor_client=debtor, amount=Decimal("100000.00"), issue_date=date.today(), due_date=date.today() + timedelta(days=30))

    @patch("mercado.views.rank_offers")
    def test_generates_and_persists_ranked_offers(self, rank_offers):
        rank_offers.return_value = [
            {"lender": {"id": 1, "name": "Financiera Uno", "risk_profile": "aggressive"}, "advance_percentage": "90.00", "rate": "2.00", "net_amount": "90000.00"},
            {"lender": {"id": 2, "name": "Financiera Dos", "risk_profile": "specialized"}, "advance_percentage": "85.00", "rate": "1.50", "net_amount": "85000.00"},
            {"lender": {"id": 3, "name": "Financiera Tres", "risk_profile": "conservative"}, "advance_percentage": "95.00", "rate": "3.00", "net_amount": "95000.00"},
        ]
        response = self.client.post(f"/api/invoices/{self.invoice.id}/offers/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(Offer.objects.filter(invoice=self.invoice).count(), 3)
        self.assertEqual(response.data[0]["category"], "best")
        self.assertEqual(response.data[0]["financing_cost"], "2000.00")
        self.assertEqual(response.data[0]["funding_time"], "Hoy mismo")

    def test_accepts_a_persisted_offer_and_funds_invoice(self):
        lender = Lender.objects.create(name="Financiera Uno", risk_profile="aggressive")
        offer = Offer.objects.create(invoice=self.invoice, lender=lender, advance_percentage=Decimal("90.00"), rate=Decimal("2.00"), net_amount=Decimal("90000.00"), financing_cost=Decimal("2000.00"), expires_at=timezone.now() + timedelta(days=1))
        response = self.client.post(f"/api/offers/{offer.id}/accept/")
        self.assertEqual(response.status_code, 200)
        offer.refresh_from_db()
        self.invoice.refresh_from_db()
        self.assertTrue(offer.is_accepted)
        self.assertEqual(self.invoice.status, Invoice.Status.FUNDED)
        offers_response = self.client.get(f"/api/invoices/{self.invoice.id}/offers/")
        self.assertEqual(offers_response.status_code, 200)
        self.assertIsNotNone(offers_response.data[0]["accepted_at"])

    def test_unknown_offer_returns_json_404(self):
        response = self.client.post("/api/offers/9999/accept/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, {"detail": "Offer not found."})
