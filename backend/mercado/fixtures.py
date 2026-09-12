"""
Hardcoded example data backing /api/invoices/<id>/offers/ and
/api/offers/<id>/accept/.

TEMPORARY: stands in for the real bidding/matching logic. See
API_CONTRACT.md and facturas/fixtures.py.
"""

LENDER_OFFER_TEMPLATES = [
    {
        "lender": {"id": 1, "name": "Financiera del Bajío", "risk_profile": "conservative"},
        "advance_percentage": "80.00",
        "rate": "2.10",
    },
    {
        "lender": {"id": 2, "name": "Capital Ágil MX", "risk_profile": "aggressive"},
        "advance_percentage": "92.00",
        "rate": "4.50",
    },
    {
        "lender": {"id": 3, "name": "Fondeo Azteca", "risk_profile": "moderate"},
        "advance_percentage": "87.00",
        "rate": "3.20",
    },
    {
        "lender": {"id": 4, "name": "Nortem Capital", "risk_profile": "moderate"},
        "advance_percentage": "85.50",
        "rate": "2.85",
    },
]
