import random
import statistics
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from empresas.models import Company, DebtorClient, PaymentHistory
from facturas.models import Invoice

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
        "Seeds one demo Company with DebtorClients (one per archetype), "
        "PaymentHistory following an archetype-appropriate distribution, "
        "and pending Invoices. Safe to re-run — clears its own demo data "
        "first instead of piling up duplicates."
    )

    def handle(self, *args, **options):
        with transaction.atomic():
            company = self._seed_company()
            clients = self._seed_debtor_clients(company)
            stats = self._seed_payment_history(clients)
            invoice_count = self._seed_invoices(company, clients)

        total_payments = sum(data["count"] for data in stats.values())
        self.stdout.write(
            self.style.SUCCESS(
                f"\nSeeded 1 company, {len(clients)} debtor clients, "
                f"{total_payments} payment history records, "
                f"{invoice_count} pending invoices.\n"
            )
        )
        self._print_summary(stats)

    def _seed_company(self):
        company, _ = Company.objects.update_or_create(
            rfc=DEMO_COMPANY["rfc"],
            defaults={
                "legal_name": DEMO_COMPANY["legal_name"],
                "is_verified": DEMO_COMPANY["is_verified"],
            },
        )
        return company

    def _seed_debtor_clients(self, company):
        # Wipe this company's existing debtor clients so re-running the
        # command gives a fresh, consistent dataset instead of piling up
        # duplicates. Cascades to PaymentHistory and Invoice automatically.
        DebtorClient.objects.filter(company=company).delete()

        return [
            DebtorClient.objects.create(company=company, name=name, archetype=archetype)
            for name, archetype in DEBTOR_CLIENTS
        ]

    def _seed_payment_history(self, clients):
        today = timezone.now().date()
        stats = {}
        for client in clients:
            n = _payment_count_for(client.archetype)
            days_late_values = [_days_late_for(client.archetype) for _ in range(n)]
            paid_at_values = _paid_at_sequence(n, today)

            PaymentHistory.objects.bulk_create(
                PaymentHistory(
                    debtor_client=client,
                    amount=_random_amount(),
                    days_late=days_late,
                    paid_at=paid_at,
                )
                for days_late, paid_at in zip(days_late_values, paid_at_values)
            )
            stats[client.id] = {
                "client": client,
                "count": n,
                "values": days_late_values,
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

    def _print_summary(self, stats):
        header = (
            f"{'Client':<32}{'Archetype':<12}{'#':>4}"
            f"{'Avg days late':>16}{'Std dev':>12}"
        )
        self.stdout.write(header)
        self.stdout.write("-" * len(header))

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

            self.stdout.write(
                f"{client.name:<32}{client.archetype:<12}{n:>4}"
                f"{avg_str:>16}{std_str:>12}"
            )
