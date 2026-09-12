import random
import statistics
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from empresas.models import Company, DebtorClient, PaymentHistory
from facturas.models import Invoice, InvoiceBatch
from financiadoras.models import Lender
from mercado.matching_engine import LENDER_IDENTITIES

DEMO_COMPANY = {
    "rfc": "GIA850101AB1",
    "legal_name": "Grupo Industrial Azteca S.A. de C.V.",
    "is_verified": True,
}

# (name, archetype) — archetype drives the payment-history distribution below.
DEBTOR_CLIENTS = [
    ("Comercializadora del Norte", "reliable"),
    ("Ferretería La Unión", "reliable"),
    ("Grupo Constructor Peninsular", "irregular"),
    ("Materiales Industriales MTY", "irregular"),
    ("Farmacias San Rafael", "delinquent"),
    ("Autotransportes del Golfo", "new"),
]

INVOICE_TERMS_DAYS = (30, 45, 60)

NESSIE_ADDRESS = {
    "street_number": "1",
    "street_name": "Av. Constitución",
    "city": "Monterrey",
    "state": "NL",
    "zip": "64000",
}


def _days_late_for(archetype):
    """Sample one days_late value matching the archetype's intended shape."""
    if archetype == "reliable":
        # Low variance, tight around a normal 30-day term.
        value = random.gauss(30, 4)
        return max(15, min(50, round(value)))
    if archetype == "irregular":
        # High variance: sometimes early, sometimes very late.
        value = random.gauss(25, 25)
        return max(-15, min(90, round(value)))
    if archetype == "delinquent":
        # Consistently late, floor at 45 so it never looks "reliable".
        value = random.gauss(58, 9)
        return max(45, min(110, round(value)))
    # "new": too little history to have a real pattern, but the couple of
    # records that exist look unremarkable.
    value = random.gauss(30, 8)
    return max(10, min(60, round(value)))


def _payment_count_for(archetype):
    if archetype == "new":
        return random.choice([0, 1, 2])
    return random.randint(8, 15)


def _random_amount(low=20000, high=350000):
    return Decimal(str(round(random.uniform(low, high), 2)))


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
        with_nessie = options["with_nessie"]
        # Imported lazily so `core.nessie_client` (and its `requests`
        # dependency) is only ever touched when actually needed.
        nessie = None
        if with_nessie:
            from core import nessie_client as nessie

        with transaction.atomic():
            company = self._seed_company()
            lenders = self._seed_lenders()

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
            invoice_count = self._seed_invoices(company, clients)

        total_payments = sum(data["count"] for data in stats.values())
        self.stdout.write(
            self.style.SUCCESS(
                f"\nSeeded 1 company, {len(lenders)} lenders, {len(clients)} "
                f"debtor clients, {total_payments} payment history records, "
                f"{invoice_count} pending invoices."
                + (" (with real Nessie records)" if with_nessie else "")
                + "\n"
            )
        )
        self._print_nessie_identities(company, lenders, with_nessie)
        self._print_summary(stats, with_nessie)

    def _seed_company(self):
        company, _ = Company.objects.update_or_create(
            rfc=DEMO_COMPANY["rfc"],
            defaults={
                "legal_name": DEMO_COMPANY["legal_name"],
                "is_verified": DEMO_COMPANY["is_verified"],
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
        # duplicates. Cascades to PaymentHistory and Invoice automatically.
        DebtorClient.objects.filter(company=company).delete()
        # InvoiceBatch has its own FK straight to Company (not through
        # DebtorClient), so it doesn't get cascade-deleted above — wipe it
        # separately or every re-seed leaves behind empty, orphaned batches.
        InvoiceBatch.objects.filter(company=company).delete()

        return [
            DebtorClient.objects.create(company=company, name=name, archetype=archetype)
            for name, archetype in DEBTOR_CLIENTS
        ]

    def _seed_payment_history(self, clients, company, nessie):
        today = timezone.now().date()
        stats = {}
        for client in clients:
            n = _payment_count_for(client.archetype)
            days_late_values = [_days_late_for(client.archetype) for _ in range(n)]
            paid_at_values = _paid_at_sequence(n, today)
            amounts = [_random_amount() for _ in range(n)]

            records = [
                PaymentHistory(
                    debtor_client=client,
                    amount=amount,
                    days_late=days_late,
                    paid_at=paid_at,
                )
                for amount, days_late, paid_at in zip(amounts, days_late_values, paid_at_values)
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
        count = random.randint(8, 15)
        today = timezone.now().date()

        invoices = []
        for _ in range(count):
            client = random.choice(clients)
            issue_date = today - timedelta(days=random.randint(5, 45))
            due_date = issue_date + timedelta(days=random.choice(INVOICE_TERMS_DAYS))
            invoices.append(
                Invoice(
                    company=company,
                    debtor_client=client,
                    amount=_random_amount(),
                    issue_date=issue_date,
                    due_date=due_date,
                    status=Invoice.Status.PENDING,
                )
            )
        Invoice.objects.bulk_create(invoices)
        return count

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
