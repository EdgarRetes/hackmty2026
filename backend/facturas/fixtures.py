"""
Hardcoded example data backing the /api/invoices/ family of endpoints.

TEMPORARY: these stand in for real database queries so the frontend has
a stable contract to build against. See API_CONTRACT.md. Swap for real
queries once Company/DebtorClient/Invoice data actually gets created.
"""

DEMO_COMPANY = {
    "id": 1,
    "legal_name": "Grupo Industrial Azteca S.A. de C.V.",
    "rfc": "GIA850101AB1",
}

DEMO_INVOICES = [
    {
        "id": 1,
        "folio": "FAC-2026-0001",
        "company": DEMO_COMPANY,
        "debtor_client": {
            "id": 1,
            "name": "Comercializadora del Norte",
            "archetype": "retail_chain",
        },
        "amount": "150000.00",
        "issue_date": "2026-08-15",
        "due_date": "2026-10-15",
        "status": "pending",
    },
    {
        "id": 2,
        "folio": "FAC-2026-0002",
        "company": DEMO_COMPANY,
        "debtor_client": {
            "id": 2,
            "name": "Grupo Constructor Peninsular",
            "archetype": "construction",
        },
        "amount": "320000.50",
        "issue_date": "2026-08-20",
        "due_date": "2026-11-20",
        "status": "pending",
    },
    {
        "id": 3,
        "folio": "FAC-2026-0003",
        "company": DEMO_COMPANY,
        "debtor_client": {
            "id": 3,
            "name": "Farmacias San Rafael",
            "archetype": "pharma_retail",
        },
        "amount": "87500.00",
        "issue_date": "2026-09-01",
        "due_date": "2026-10-01",
        "status": "pending",
    },
    {
        "id": 4,
        "folio": "FAC-2026-0004",
        "company": DEMO_COMPANY,
        "debtor_client": {
            "id": 4,
            "name": "Autotransportes del Golfo",
            "archetype": "logistics",
        },
        "amount": "45250.75",
        "issue_date": "2026-09-05",
        "due_date": "2026-10-20",
        "status": "pending",
    },
]


def get_invoice(invoice_id):
    return next((inv for inv in DEMO_INVOICES if inv["id"] == invoice_id), None)
