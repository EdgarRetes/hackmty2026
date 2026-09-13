import random
import statistics
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import UserProfile
from empresas.models import Company, DebtorClient, PaymentHistory
from facturas.models import Invoice, InvoiceBatch
from financiadoras.models import Lender
from mercado.matching_engine import LENDER_IDENTITIES, rank_offers
from mercado.models import Offer

# Mirrors mercado/views.py::FUNDING_TIMES — duplicated here (rather than
# imported) so seeding doesn't reach into that view module's internals;
# keep the two in sync if the funding-time copy ever changes.
FUNDING_TIMES = {
    "conservative": "48 horas",
    "aggressive": "Hoy mismo",
    "specialized": "24 horas",
}

DEMO_PROFILES = {
    "empresa": {"username": "lucia.martinez", "first_name": "Lucía", "last_name": "Martínez"},
    "financiadora": {"username": "carlos.mendoza", "first_name": "Carlos", "last_name": "Mendoza"},
}

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
            financed = self._seed_financings(invoices)

        pending_count = len(invoices) - len(financed)
        total_payments = sum(data["count"] for data in stats.values())
        self.stdout.write(
            self.style.SUCCESS(
                f"\nSeeded 1 company, {len(lenders)} lenders, 2 role profiles, "
                f"{len(clients)} debtor clients, {total_payments} payment "
                f"history records, {pending_count} pending invoices, "
                f"{len(financed)} already-financed invoices."
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
        # Postgres's bulk_create returns objects with real pks populated,
        # which _seed_financings below needs to run the pricing pipeline
        # against specific invoices.
        return Invoice.objects.bulk_create(invoices)

    def _seed_financings(self, invoices):
        """
        Marks a few freshly-seeded invoices as already financed: runs the
        real pricing pipeline, persists all 3 offers exactly like
        POST /api/invoices/{id}/offers/ does, then accepts the best one.
        Without this, the Financiadora role's "Financiamientos" page
        (frontend/src/lib/financing.ts) — which reads real accepted
        Offers, not mock data — has nothing to show until a real user
        clicks through the accept flow at least once.
        """
        if len(invoices) < 3:
            return []

        today = timezone.now()
        financed = []

        for index, invoice in enumerate(random.sample(invoices, 3)):
            ranked = rank_offers(invoice)
            rates = [Decimal(str(quote["rate"])) for quote in ranked]
            advances = [Decimal(str(quote["advance_percentage"])) for quote in ranked]
            amount = Decimal(str(invoice.amount))
            best_offer = None

            for rank, quote in enumerate(ranked, start=1):
                lender_data = quote["lender"]
                lender, _ = Lender.objects.update_or_create(
                    pk=lender_data["id"],
                    defaults={
                        "name": lender_data["name"],
                        "risk_profile": lender_data["risk_profile"],
                        "is_verified": True,
                    },
                )
                rate = Decimal(str(quote["rate"]))
                advance = Decimal(str(quote["advance_percentage"]))
                if rank == 1:
                    category = "best"
                elif rate == min(rates):
                    category = "lowest_rate"
                elif advance == max(advances):
                    category = "highest_advance"
                else:
                    category = "fastest"
                financing_cost = (amount * rate / Decimal("100")).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )

                offer, _ = Offer.objects.update_or_create(
                    invoice=invoice,
                    lender=lender,
                    defaults={
                        "advance_percentage": advance,
                        "rate": rate,
                        "net_amount": Decimal(str(quote["net_amount"])),
                        "financing_cost": financing_cost,
                        "funding_time": FUNDING_TIMES[lender.risk_profile],
                        "category": category,
                        "rank": rank,
                        "expires_at": today + timedelta(hours=24),
                    },
                )
                if rank == 1:
                    best_offer = offer

            best_offer.is_accepted = True
            best_offer.accepted_at = today - timedelta(days=random.randint(3, 30))
            best_offer.save(update_fields=["is_accepted", "accepted_at"])

            # First one "paid" (fully settled), the rest "funded" (still
            # active) — exercises both status buckets on the Financing page.
            invoice.status = Invoice.Status.PAID if index == 0 else Invoice.Status.FUNDED
            invoice.save(update_fields=["status"])
            financed.append(invoice)

        return financed

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
