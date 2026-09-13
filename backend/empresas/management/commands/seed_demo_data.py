import random
import statistics
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import UserProfile
from core.risk_engine import assess_invoice
from empresas.models import Company, DebtorClient, PaymentHistory
from facturas.models import Invoice, InvoiceBatch
from financiadoras.models import Lender
from mercado.matching_engine import LENDER_IDENTITIES
from mercado.models import Offer

DEMO_PROFILES = {
    "empresa": {"username": "lucia.martinez", "first_name": "Lucía", "last_name": "Martínez"},
    "financiadora": {"username": "carlos.mendoza", "first_name": "Carlos", "last_name": "Mendoza"},
}

DEMO_COMPANY = {
    "rfc": "GIA850101AB1",
    "legal_name": "Grupo Industrial Azteca S.A. de C.V.",
    "is_verified": True,
    "scian_sector": "333",
    "years_operating": 12,
    "annual_revenue": Decimal("12000000.00"),
    "dispute_rate": Decimal("0.01000"),
    "dilution_rate": Decimal("0.01000"),
    "data_source": "INEGI DENUE / mock hackathon",
    "source_reference": "https://www.inegi.org.mx/servicios/api_denue.html",
}

# Deterministic synthetic snapshots shaped like DENUE and bureau inputs.
DEBTOR_CLIENTS = [
    {"name": "Comercializadora del Norte", "archetype": "reliable", "rfc": "CDN010101AA1", "scian_sector": "461", "employee_band": "51-100", "years_operating": 14, "bureau_score": 740, "current_ratio": Decimal("1.90"), "debt_to_ebitda": Decimal("1.80"), "operating_margin": Decimal("0.13000"), "history": [0, 0, 1, 0, 2, 0]},
    {"name": "Farmacias San Rafael", "archetype": "delinquent", "rfc": "FSR010101AA2", "scian_sector": "464", "employee_band": "101-250", "years_operating": 6, "bureau_score": 430, "current_ratio": Decimal("0.60"), "debt_to_ebitda": Decimal("7.00"), "operating_margin": Decimal("-0.05000"), "has_legal_events": True, "history": [60, 75, 90, 95, 110, 120], "defaults": {3, 4, 5}},
    {"name": "Manufacturas Regiomontanas", "archetype": "reliable", "rfc": "MRE010101AA3", "scian_sector": "333", "employee_band": "31-50", "years_operating": 9, "bureau_score": 710, "current_ratio": Decimal("1.60"), "debt_to_ebitda": Decimal("2.30"), "operating_margin": Decimal("0.10000"), "history": [0, 0, 0, 1, 0]},
    {"name": "Logística Nueva Era", "archetype": "new", "rfc": "LNE010101AA4", "scian_sector": "484", "employee_band": "6-10", "years_operating": 1, "bureau_score": None, "current_ratio": Decimal("1.20"), "debt_to_ebitda": Decimal("3.00"), "operating_margin": Decimal("0.06000"), "history": []},
]

INVOICE_TERMS_DAYS = (30, 45, 60)

NESSIE_ADDRESS = {
    "street_number": "1",
    "street_name": "Av. Constitución",
    "city": "Monterrey",
    "state": "NL",
    "zip": "64000",
}


def _paid_at_sequence(n, today, most_recent_offset=20):
    """
    n dates in ascending (oldest-first) order, spaced ~25-65 days apart —
    roughly one invoice cycle — with the most recent one `most_recent_offset`
    days before today, so there's a realistic gap to measure recency from.
    """
    dates = []
    cursor = today - timedelta(days=most_recent_offset)
    for _ in range(n):
        dates.append(cursor)
        cursor -= timedelta(days=random.randint(25, 65))
    dates.reverse()
    return dates


class Command(BaseCommand):
    help = (
        "Seeds one demo Company, three demo Lenders, DebtorClients (one "
        "per archetype), PaymentHistory following an archetype-appropriate "
        "distribution, and pending Invoices. Safe to re-run — clears its "
        "own demo data first instead of piling up duplicates. Pass "
        "--with-nessie to also provision real Nessie sandbox customers/"
        "accounts for the Company and Lenders, and back each PaymentHistory "
        "record with a real Nessie deposit (see NESSIE_EXPLORATION.md)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--with-nessie",
            action="store_true",
            help="Also provision real Nessie sandbox customers/accounts/deposits.",
        )

    def handle(self, *args, **options):
        random.seed(20260912)
        with_nessie = options["with_nessie"]
        # Imported lazily so `core.nessie_client` (and its `requests`
        # dependency) is only ever touched when actually needed.
        nessie = None
        if with_nessie:
            from core import nessie_client as nessie

        with transaction.atomic():
            company = self._seed_company()
            lenders = self._seed_lenders()
            self._seed_profiles(company, lenders)

            if with_nessie:
                self._provision_nessie_identity(nessie, company)
                for lender in lenders:
                    self._provision_nessie_identity(nessie, lender)

            stale_deposit_ids = list(
                PaymentHistory.objects.filter(debtor_client__company=company)
                .exclude(nessie_deposit_id="")
                .values_list("nessie_deposit_id", flat=True)
            )

            clients = self._seed_debtor_clients(company)

            if with_nessie and stale_deposit_ids:
                for deposit_id in stale_deposit_ids:
                    nessie.delete_deposit(deposit_id)

            stats = self._seed_payment_history(clients, company, nessie if with_nessie else None)
            invoices = self._seed_invoices(company, clients)
            assessments = [assess_invoice(invoice) for invoice in invoices]
            invoice_count = len(invoices)

        total_payments = sum(data["count"] for data in stats.values())
        self.stdout.write(
            self.style.SUCCESS(
                f"\nSeeded 1 company, {len(lenders)} lenders, 2 role profiles, "
                f"{len(clients)} debtor clients, {total_payments} payment "
                f"history records, {invoice_count} pending invoices."
                + (" (with real Nessie records)" if with_nessie else "")
                + "\n"
            )
        )
        self._print_nessie_identities(company, lenders, with_nessie)
        self._print_summary(stats, with_nessie)
        self.stdout.write("\nUnderwriting scenarios")
        for assessment in assessments:
            self.stdout.write(
                f"  {assessment.invoice.demo_scenario:<22} "
                f"{assessment.decision:<8} rating={assessment.rating}"
            )

    def _seed_company(self):
        company, _ = Company.objects.update_or_create(
            rfc=DEMO_COMPANY["rfc"],
            defaults={
                "legal_name": DEMO_COMPANY["legal_name"],
                "is_verified": DEMO_COMPANY["is_verified"],
                "scian_sector": DEMO_COMPANY["scian_sector"],
                "years_operating": DEMO_COMPANY["years_operating"],
                "annual_revenue": DEMO_COMPANY["annual_revenue"],
                "dispute_rate": DEMO_COMPANY["dispute_rate"],
                "dilution_rate": DEMO_COMPANY["dilution_rate"],
                "data_source": DEMO_COMPANY["data_source"],
                "source_reference": DEMO_COMPANY["source_reference"],
                "data_as_of": timezone.localdate(),
            },
        )
        return company

    def _seed_lenders(self):
        return [
            Lender.objects.update_or_create(
                name=identity["name"],
                defaults={"risk_profile": identity["risk_profile"], "is_verified": True},
            )[0]
            for identity in LENDER_IDENTITIES.values()
        ]

    def _seed_profiles(self, company, lenders):
        """
        One demo Django User + UserProfile per role, so the frontend's
        role switcher (GET /api/profiles/) reads real identities instead
        of a hardcoded name. Idempotent — reruns just update the same two
        users rather than creating duplicates.
        """
        User = get_user_model()

        empresa_info = DEMO_PROFILES["empresa"]
        empresa_user, _ = User.objects.update_or_create(
            username=empresa_info["username"],
            defaults={
                "first_name": empresa_info["first_name"],
                "last_name": empresa_info["last_name"],
            },
        )
        UserProfile.objects.update_or_create(
            user=empresa_user,
            defaults={
                "role": UserProfile.Role.EMPRESA,
                "display_name": f"{empresa_info['first_name']} {empresa_info['last_name']}",
                "company": company,
                "lender": None,
            },
        )

        financiadora_info = DEMO_PROFILES["financiadora"]
        financiadora_user, _ = User.objects.update_or_create(
            username=financiadora_info["username"],
            defaults={
                "first_name": financiadora_info["first_name"],
                "last_name": financiadora_info["last_name"],
            },
        )
        UserProfile.objects.update_or_create(
            user=financiadora_user,
            defaults={
                "role": UserProfile.Role.FINANCIADORA,
                "display_name": f"{financiadora_info['first_name']} {financiadora_info['last_name']}",
                "company": None,
                "lender": lenders[0] if lenders else None,
            },
        )

    def _provision_nessie_identity(self, nessie, entity):
        """
        Idempotent: reuses entity.nessie_customer_id/nessie_account_id if
        already set (from a previous --with-nessie run), so re-seeding
        doesn't create duplicate customers in the shared Nessie sandbox.
        """
        display_name = entity.legal_name if hasattr(entity, "legal_name") else entity.name
        changed = False

        if not entity.nessie_customer_id:
            entity.nessie_customer_id = nessie.create_customer(
                first_name="Factorai",
                last_name=display_name,
                address=NESSIE_ADDRESS,
            )
            changed = True

        if not entity.nessie_account_id:
            entity.nessie_account_id = nessie.create_account(
                customer_id=entity.nessie_customer_id,
                account_type="Checking",
                nickname=f"{display_name} (factorai demo)",
                balance=0,
            )
            changed = True

        if changed:
            entity.save(update_fields=["nessie_customer_id", "nessie_account_id"])

    def _seed_debtor_clients(self, company):
        # Wipe this company's existing debtor clients so re-running the
        # command gives a fresh, consistent dataset instead of piling up
        # duplicates. Offers protect their assessment snapshot, so they must
        # be removed before invoices and debtor clients can cascade safely.
        Offer.objects.filter(invoice__company=company).delete()
        DebtorClient.objects.filter(company=company).delete()
        # InvoiceBatch has its own FK straight to Company (not through
        # DebtorClient), so it doesn't get cascade-deleted above — wipe it
        # separately or every re-seed leaves behind empty, orphaned batches.
        InvoiceBatch.objects.filter(company=company).delete()

        clients = []
        for spec in DEBTOR_CLIENTS:
            values = {
                key: value
                for key, value in spec.items()
                if key not in {"history", "defaults"}
            }
            values.update(
                company=company,
                data_source="INEGI DENUE / bureau mock hackathon",
                source_reference="https://www.inegi.org.mx/servicios/api_denue.html",
                data_as_of=timezone.localdate(),
            )
            clients.append(DebtorClient.objects.create(**values))
        return clients

    def _seed_payment_history(self, clients, company, nessie):
        today = timezone.localdate()
        stats = {}
        specs_by_rfc = {spec["rfc"]: spec for spec in DEBTOR_CLIENTS}
        for client in clients:
            spec = specs_by_rfc[client.rfc]
            days_late_values = list(spec["history"])
            n = len(days_late_values)
            due_at_values = _paid_at_sequence(n, today, most_recent_offset=45)
            issued_at_values = [due_at - timedelta(days=30) for due_at in due_at_values]
            paid_at_values = [due_at + timedelta(days=dpd) for due_at, dpd in zip(due_at_values, days_late_values)]
            amounts = [Decimal("100000.00") for _ in range(n)]
            defaults = spec.get("defaults", set())

            records = [
                PaymentHistory(
                    debtor_client=client,
                    amount=amount,
                    amount_paid=amount if index not in defaults else Decimal("0.00"),
                    days_late=days_late,
                    issued_at=issued_at,
                    due_at=due_at,
                    paid_at=paid_at,
                    is_default=index in defaults,
                )
                for index, (amount, days_late, issued_at, due_at, paid_at) in enumerate(
                    zip(amounts, days_late_values, issued_at_values, due_at_values, paid_at_values)
                )
            ]

            nessie_linked = 0
            if nessie is not None and company.nessie_account_id:
                for record in records:
                    record.nessie_deposit_id = nessie.create_deposit(
                        account_id=company.nessie_account_id,
                        amount=float(record.amount),
                        transaction_date=record.paid_at.isoformat(),
                        description=f"Payment from {client.name} ({client.archetype})",
                    )
                    nessie_linked += 1

            PaymentHistory.objects.bulk_create(records)
            stats[client.id] = {
                "client": client,
                "count": n,
                "values": days_late_values,
                "nessie_linked": nessie_linked,
            }
        return stats

    def _seed_invoices(self, company, clients):
        today = timezone.localdate()
        client_by_rfc = {client.rfc: client for client in clients}
        scenarios = [
            ("approved", "CDN010101AA1", Decimal("200000.00"), 45, "vigente", False),
            ("risk_rejected", "FSR010101AA2", Decimal("350000.00"), 60, "vigente", False),
            ("eligibility_rejected", "MRE010101AA3", Decimal("180000.00"), 45, "cancelado", False),
            ("manual_review", "LNE010101AA4", Decimal("90000.00"), 30, "vigente", False),
        ]
        invoices = []
        for index, (scenario, debtor_rfc, amount, term, sat_status, assigned) in enumerate(scenarios, start=1):
            debtor = client_by_rfc[debtor_rfc]
            invoices.append(
                Invoice.objects.create(
                    company=company,
                    debtor_client=debtor,
                    amount=amount,
                    outstanding_balance=amount,
                    issue_date=today - timedelta(days=5),
                    due_date=today + timedelta(days=term),
                    status=Invoice.Status.PENDING,
                    cfdi_uuid=f"00000000-0000-4000-8000-{index:012d}",
                    issuer_rfc=company.rfc,
                    receiver_rfc=debtor.rfc,
                    currency="MXN",
                    payment_method="PPD",
                    sat_status=sat_status,
                    sat_verified_at=timezone.now(),
                    xml_hash=f"{index:064x}",
                    is_previously_assigned=assigned,
                    has_delivery_evidence=True,
                    demo_scenario=scenario,
                )
            )
        return invoices

    def _print_nessie_identities(self, company, lenders, with_nessie):
        if not with_nessie:
            self.stdout.write("Nessie: skipped (pass --with-nessie to provision real records)\n")
            return

        header = f"{'Entity':<40}{'Nessie customer':<39}{'Nessie account':<39}"
        self.stdout.write(header)
        self.stdout.write("-" * len(header))
        self.stdout.write(
            f"{company.legal_name:<40}{company.nessie_customer_id:<39}{company.nessie_account_id:<39}"
        )
        for lender in lenders:
            self.stdout.write(
                f"{lender.name:<40}{lender.nessie_customer_id:<39}{lender.nessie_account_id:<39}"
            )
        self.stdout.write("")

    def _print_summary(self, stats, with_nessie):
        columns = f"{'Client':<32}{'Archetype':<12}{'#':>4}{'Avg days late':>16}{'Std dev':>12}"
        if with_nessie:
            columns += f"{'Nessie deposits':>18}"
        self.stdout.write(columns)
        self.stdout.write("-" * len(columns))

        for data in stats.values():
            client = data["client"]
            values = data["values"]
            n = data["count"]

            if n == 0:
                avg_str, std_str = "—", "—"
            elif n == 1:
                avg_str, std_str = f"{values[0]:.1f}", "n/a"
            else:
                avg_str = f"{statistics.mean(values):.1f}"
                std_str = f"{statistics.stdev(values):.1f}"

            row = (
                f"{client.name:<32}{client.archetype:<12}{n:>4}"
                f"{avg_str:>16}{std_str:>12}"
            )
            if with_nessie:
                linked_str = f"{data['nessie_linked']}/{n}"
                row += f"{linked_str:>18}"
            self.stdout.write(row)
