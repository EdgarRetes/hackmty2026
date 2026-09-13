from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from facturas.models import Invoice
from financiadoras.models import Lender
from mercado.models import Offer


class DemoSeedTests(TestCase):
    def test_seed_is_idempotent_and_covers_every_underwriting_decision(self):
        output = StringIO()

        call_command("seed_demo_data", stdout=output)
        approved = Invoice.objects.get(demo_scenario="approved")
        Offer.objects.create(
            invoice=approved,
            risk_assessment=approved.risk_assessments.first(),
            lender=Lender.objects.first(),
            advance_percentage="95.00",
            rate="1.50",
        )
        call_command("seed_demo_data", stdout=output)

        scenarios = {
            invoice.demo_scenario: invoice.risk_assessments.first().decision
            for invoice in Invoice.objects.exclude(demo_scenario="")
        }
        self.assertEqual(
            scenarios,
            {
                "approved": "APPROVE",
                "risk_rejected": "REJECT",
                "eligibility_rejected": "REJECT",
                "manual_review": "REVIEW",
            },
        )
        approved = Invoice.objects.get(demo_scenario="approved")
        self.assertEqual(approved.risk_assessments.first().term_days, 45)
