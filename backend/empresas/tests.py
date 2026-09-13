from datetime import date
from decimal import Decimal

from django.test import TestCase

from .models import Company, DebtorClient, PaymentHistory


class PaymentHistoryTests(TestCase):
    def test_days_past_due_uses_due_date_not_invoice_term(self):
        company = Company.objects.create(
            rfc="TST010101AA1", legal_name="Empresa de prueba"
        )
        debtor = DebtorClient.objects.create(
            company=company, name="Pagador de prueba", archetype="reliable"
        )
        payment = PaymentHistory.objects.create(
            debtor_client=debtor,
            amount=Decimal("100000.00"),
            amount_paid=Decimal("100000.00"),
            issued_at=date(2026, 1, 1),
            due_at=date(2026, 1, 31),
            paid_at=date(2026, 2, 5),
        )

        self.assertEqual(payment.days_past_due, 5)

    def test_days_past_due_is_zero_for_early_payment(self):
        company = Company.objects.create(
            rfc="TST010101AA2", legal_name="Empresa de prueba dos"
        )
        debtor = DebtorClient.objects.create(
            company=company, name="Pagador puntual", archetype="reliable"
        )
        payment = PaymentHistory.objects.create(
            debtor_client=debtor,
            amount=Decimal("50000.00"),
            amount_paid=Decimal("50000.00"),
            issued_at=date(2026, 1, 1),
            due_at=date(2026, 1, 31),
            paid_at=date(2026, 1, 25),
        )

        self.assertEqual(payment.days_past_due, 0)
