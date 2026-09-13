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
    "scian_sector": "333",
    "years_operating": 12,
    "annual_revenue": Decimal("12000000.00"),
    "dispute_rate": Decimal("0.01000"),
    "dilution_rate": Decimal("0.01000"),
    "data_source": "INEGI DENUE / mock hackathon",
    "source_reference": "https://www.inegi.org.mx/servicios/api_denue.html",
}

def _debtor_spec(name, archetype, rfc, scian_sector, **overrides):
    profiles = {
        "reliable": {"employee_band": "51-100", "years_operating": 10, "bureau_score": 720, "current_ratio": Decimal("1.70"), "debt_to_ebitda": Decimal("2.10"), "operating_margin": Decimal("0.11000"), "history": [0, 0, 1, 0, 2, 0]},
        "irregular": {"employee_band": "31-50", "years_operating": 6, "bureau_score": 610, "current_ratio": Decimal("1.10"), "debt_to_ebitda": Decimal("4.20"), "operating_margin": Decimal("0.05000"), "history": [5, 15, 30, 0, 45, 10]},
        "delinquent": {"employee_band": "101-250", "years_operating": 6, "bureau_score": 430, "current_ratio": Decimal("0.60"), "debt_to_ebitda": Decimal("7.00"), "operating_margin": Decimal("-0.05000"), "has_legal_events": True, "history": [60, 75, 90, 95, 110, 120], "defaults": {3, 4, 5}},
        "new": {"employee_band": "6-10", "years_operating": 1, "bureau_score": None, "current_ratio": Decimal("1.20"), "debt_to_ebitda": Decimal("3.00"), "operating_margin": Decimal("0.06000"), "history": []},
    }
    return {"name": name, "archetype": archetype, "rfc": rfc, "scian_sector": scian_sector, **profiles[archetype], **overrides}


# Deterministic synthetic snapshots shaped like DENUE and bureau inputs.
DEBTOR_CLIENTS = [
    _debtor_spec("Comercializadora del Norte", "reliable", "CDN010101AA1", "461", years_operating=14, bureau_score=740, current_ratio=Decimal("1.90"), debt_to_ebitda=Decimal("1.80"), operating_margin=Decimal("0.13000"), history=[0, 0, 1, 0, 2, 0]),
    _debtor_spec("Farmacias San Rafael", "delinquent", "FSR010101AA2", "464"),
    _debtor_spec("Manufacturas Regiomontanas", "reliable", "MRE010101AA3", "333", years_operating=9, bureau_score=710, current_ratio=Decimal("1.60"), debt_to_ebitda=Decimal("2.30"), operating_margin=Decimal("0.10000"), history=[0, 0, 0, 1, 0]),
    _debtor_spec("Logística Nueva Era", "new", "LNE010101AA4", "484"),
    _debtor_spec("Ferretería La Unión", "reliable", "FLU010101AA5", "467"),
    _debtor_spec("Distribuidora Regia", "reliable", "DRE010101AA6", "431"),
    _debtor_spec("Aceros del Norte", "reliable", "ADN010101AA7", "331"),
    _debtor_spec("TecnoSoluciones del Norte", "reliable", "TSN010101AA8", "541"),
    _debtor_spec("Grupo Constructor Peninsular", "irregular", "GCP010101AA9", "236"),
    _debtor_spec("Materiales Industriales MTY", "irregular", "MIM010101AB1", "434"),
    _debtor_spec("Transportes Fronterizos", "irregular", "TFR010101AB2", "484"),
    _debtor_spec("Insumos Médicos MTY", "irregular", "IMM010101AB3", "464"),
    _debtor_spec("Papelería Escolar MTY", "irregular", "PEM010101AB4", "465"),
    _debtor_spec("Constructora Sierra Madre", "delinquent", "CSM010101AB5", "236"),
    _debtor_spec("Textiles Cumbres", "delinquent", "TCU010101AB6", "313"),
    _debtor_spec("Autotransportes del Golfo", "new", "ADG010101AB7", "484"),
    _debtor_spec("AgroIndustrias Nuevo León", "new", "AIN010101AB8", "115"),
    _debtor_spec("Hotelera Regiomontana", "new", "HRE010101AB9", "721"),
]

INVOICE_TERMS_DAYS = (30, 45, 60)

NESSIE_ADDRESS = {
    "street_number": "1",
    "street_name": "Av. Constitución",
    "city": "Monterrey",
    "state": "NL",
    "zip": "64000",
}


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
            assessments = {invoice.pk: assess_invoice(invoice) for invoice in invoices}
            available_ids = [
                invoice.pk
                for invoice in invoices
                if assessments[invoice.pk].decision == "APPROVE"
            ]
            Invoice.objects.filter(pk__in=available_ids).update(status=Invoice.Status.AVAILABLE)
            for invoice in invoices:
                if invoice.pk in available_ids:
                    invoice.status = Invoice.Status.AVAILABLE
            financed = self._seed_financings(invoices, assessments)
            financed_ids = {invoice.pk for invoice in financed}
            publishable = [
                invoice
                for invoice in invoices
                if invoice.pk not in financed_ids
                and assessments[invoice.pk].decision == "APPROVE"
                and invoice.demo_scenario != "approved"
            ]
            published_batches = self._seed_publications(company, publishable)

        available_count = Invoice.objects.filter(status=Invoice.Status.AVAILABLE).count()
        total_payments = sum(data["count"] for data in stats.values())
        self.stdout.write(
            self.style.SUCCESS(
                f"\nSeeded 1 company, {len(lenders)} lenders, 2 role profiles, "
                f"{len(clients)} debtor clients, {total_payments} payment "
                f"history records, {available_count} available invoices "
                f"({published_batches} publicaciones), "
                f"{len(financed)} already-financed invoices."
                + (" (with real Nessie records)" if with_nessie else "")
                + "\n"
            )
        )
        self._print_nessie_identities(company, lenders, with_nessie)
        self._print_summary(stats, with_nessie)
        self.stdout.write("\nUnderwriting scenarios")
        for assessment in assessments.values():
            if not assessment.invoice.demo_scenario:
                continue
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
                defaults={
                    "risk_profile": identity["risk_profile"],
                    "is_verified": True,
                    "available_capital": _random_amount(low=2_000_000, high=6_000_000),
                },
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

        target_count = random.randint(45, 65)
        for index in range(len(invoices) + 1, target_count + 1):
            debtor = random.choice(clients)
            amount = _random_amount()
            term = random.choice(INVOICE_TERMS_DAYS)
            invoices.append(
                Invoice.objects.create(
                    company=company,
                    debtor_client=debtor,
                    amount=amount,
                    outstanding_balance=amount,
                    issue_date=today - timedelta(days=random.randint(5, 45)),
                    due_date=today + timedelta(days=term),
                    status=Invoice.Status.PENDING,
                    cfdi_uuid=f"10000000-0000-4000-8000-{index:012d}",
                    issuer_rfc=company.rfc,
                    receiver_rfc=debtor.rfc,
                    currency="MXN",
                    payment_method="PPD",
                    sat_status="vigente",
                    sat_verified_at=timezone.now(),
                    xml_hash=f"{index + 1000:064x}",
                    has_delivery_evidence=True,
                )
            )
        return invoices

    def _seed_financings(self, invoices, assessments):
        """
        Marks a chunk of freshly-seeded invoices as already financed: runs
        the real pricing pipeline, persists all 3 offers exactly like
        POST /api/invoices/{id}/offers/ does, then accepts the best one,
        with accepted_at spread over the trailing ~5 months so the
        Financiadora dashboard's capital-history chart has real
        multi-month data instead of everything landing in one bucket.
        Without this, the Financiadora role's "Financiamientos" page and
        portfolio dashboard — which read real accepted Offers, not mock
        data — have nothing to show until a real user clicks through the
        accept flow at least once.
        """
        candidates = [
            invoice
            for invoice in invoices
            if assessments[invoice.pk].decision == "APPROVE"
            and invoice.demo_scenario != "approved"
        ]
        sample_size = min(len(candidates), random.randint(12, 18))
        if sample_size < 3:
            return []

        today = timezone.now()
        financed = []

        for invoice in random.sample(candidates, sample_size):
            assessment = assessments[invoice.pk]
            ranked = rank_offers(invoice, assessment)
            rates = [Decimal(str(quote["rate"])) for quote in ranked]
            advances = [Decimal(str(quote["advance_percentage"])) for quote in ranked]
            portfolio_offer = None

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
                financing_cost = Decimal(str(quote["financing_cost"]))

                offer, _ = Offer.objects.update_or_create(
                    invoice=invoice,
                    lender=lender,
                    defaults={
                        "advance_percentage": advance,
                        "rate": rate,
                        "risk_assessment": assessment,
                        "net_amount": Decimal(str(quote["net_amount"])),
                        "financing_cost": financing_cost,
                        "funding_time": FUNDING_TIMES[lender.risk_profile],
                        "category": category,
                        "rank": rank,
                        "expires_at": today + timedelta(hours=24),
                    },
                )
                if lender.pk == LENDER_IDENTITIES["conservative"]["id"]:
                    portfolio_offer = offer

            portfolio_offer.is_accepted = True
            # Spread over ~5 months so the capital-history chart has real
            # multi-month buckets instead of everything landing this week.
            portfolio_offer.accepted_at = today - timedelta(days=random.randint(3, 150))
            portfolio_offer.save(update_fields=["is_accepted", "accepted_at"])

            # Mix of "paid" (fully settled — realized return) and "funded"
            # (still active) — exercises both status buckets on the
            # Financing page and the portfolio's active-vs-completed split.
            invoice.status = (
                Invoice.Status.PAID if random.random() < 0.4 else Invoice.Status.FUNDED
            )
            invoice.save(update_fields=["status"])
            financed.append(invoice)

        return financed

    def _seed_publications(self, company, invoices):
        """
        Publishes most of the remaining (not already financed) pending
        invoices as real publicaciones (InvoiceBatch — 1 to 4 invoices
        each), so the Financiadora Marketplace has real opportunities out
        of the box. A minority are deliberately left unpublished so the
        empresa's own Facturas page still shows a genuine "No aplica"
        bucket alongside "Publicadas".
        """
        pool = list(invoices)
        random.shuffle(pool)
        to_publish = pool[: int(len(pool) * 0.8)]

        published_batches = 0
        index = 0
        while index < len(to_publish):
            size = random.choice([1, 1, 2, 2, 3, 4])
            chunk = to_publish[index : index + size]
            index += size
            if not chunk:
                continue
            batch = InvoiceBatch.objects.create(company=company)
            Invoice.objects.filter(pk__in=[invoice.pk for invoice in chunk]).update(
                batch=batch, status=Invoice.Status.IN_AUCTION
            )
            published_batches += 1

        return published_batches

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
