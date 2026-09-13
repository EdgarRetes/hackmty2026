from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from facturas.models import Invoice


class DemoSeedTests(TestCase):
    def test_seed_is_idempotent_and_covers_every_underwriting_decision(self):
        output = StringIO()

        call_command("seed_demo_data", stdout=output)
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
