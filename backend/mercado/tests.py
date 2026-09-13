from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from empresas.models import Company, DebtorClient, PaymentHistory
from facturas.models import Invoice, InvoiceBatch
from financiadoras.models import Lender

from .matching_engine import opportunity_summary
from .models import Offer


class OffersApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        company = Company.objects.create(
            rfc="TST010101AA1",
            legal_name="Empresa Real",
            is_verified=True,
            annual_revenue=Decimal("8000000.00"),
            dilution_rate=Decimal("0.01000"),
        )
        debtor = DebtorClient.objects.create(
            company=company,
            name="Cliente Real",
            archetype="reliable",
            rfc="CLI010101AA1",
            bureau_score=720,
            current_ratio=Decimal("1.80"),
            debt_to_ebitda=Decimal("2.00"),
            operating_margin=Decimal("0.12000"),
        )
        for index, dpd in enumerate([0, 0, 1, 0, 2, 0]):
            due_at = date.today() - timedelta(days=240 - index * 30)
            PaymentHistory.objects.create(
                debtor_client=debtor,
                amount=Decimal("100000.00"),
                amount_paid=Decimal("100000.00"),
                issued_at=due_at - timedelta(days=30),
                due_at=due_at,
                paid_at=due_at + timedelta(days=dpd),
            )
        self.invoice = Invoice.objects.create(
            company=company,
            debtor_client=debtor,
            amount=Decimal("100000.00"),
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            cfdi_uuid="11111111-1111-4111-8111-111111111111",
            issuer_rfc=company.rfc,
            receiver_rfc=debtor.rfc,
            xml_hash="approved-invoice-hash",
        )

    def test_generates_and_persists_term_priced_offers(self):
        response = self.client.post(f"/api/invoices/{self.invoice.id}/offers/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(Offer.objects.filter(invoice=self.invoice).count(), 3)
        self.assertEqual(response.data[0]["category"], "best")
        self.assertGreater(Decimal(response.data[0]["financing_cost"]), Decimal("0"))
        self.assertIsNotNone(Offer.objects.get(pk=response.data[0]["id"]).risk_assessment)

    def test_rejected_invoice_generates_no_offers(self):
        self.invoice.sat_status = "cancelado"
        self.invoice.save(update_fields=["sat_status"])

        response = self.client.post(f"/api/invoices/{self.invoice.id}/offers/")

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.data["assessment"]["decision"], "REJECT")
        self.assertEqual(Offer.objects.filter(invoice=self.invoice).count(), 0)

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

    def test_marketplace_summary_uses_the_current_risk_assessment(self):
        summary = opportunity_summary(self.invoice)

        self.assertEqual(summary["risk"], "low")
        self.assertGreater(Decimal(summary["estimated_return_rate"]), Decimal("0"))

    def test_accepting_a_batch_offer_persists_its_risk_assessment(self):
        batch = InvoiceBatch.objects.create(company=self.invoice.company)
        self.invoice.batch = batch
        self.invoice.status = Invoice.Status.IN_AUCTION
        self.invoice.save(update_fields=["batch", "status"])
        lender = Lender.objects.create(
            pk=1,
            name="Financiera del Bajío",
            risk_profile="conservative",
        )

        response = self.client.post(
            f"/api/invoice-batches/{batch.id}/accept/",
            {"lender_id": lender.id},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        offer = Offer.objects.get(invoice=self.invoice, lender=lender)
        self.assertIsNotNone(offer.risk_assessment)
        self.assertGreater(offer.financing_cost, Decimal("0"))
