# API Contract (mocked endpoints)

**Status: all three endpoints below return hardcoded example data.** No
database queries happen yet — this document describes the exact shape
the frontend can build against today. When the real logic lands, the
shape described here is the target; if a field ever needs to change,
this file gets updated in the same PR.

Base URL locally: `http://localhost:8000`. All request/response bodies
are JSON. Money fields (`amount`, `net_amount`, `advance_percentage`,
`rate`) are **strings**, not numbers — that's how DRF's `DecimalField`
serializes by default, and it'll stay a string once real serializers
replace this fixture data. Parse with a decimal-safe parser on the
frontend, not `parseFloat` if you can help it (floating point rounding
on money).

---

## `GET /api/invoices/`

Returns the list of pending invoices for a single demo company (no
auth/company filtering yet — every invoice belongs to the same hardcoded
`company`).

**Request**: no params, no body.

**Response**: `200 OK`, a JSON array of invoice objects.

```json
[
  {
    "id": 1,
    "folio": "FAC-2026-0001",
    "company": {
      "id": 1,
      "legal_name": "Grupo Industrial Azteca S.A. de C.V.",
      "rfc": "GIA850101AB1"
    },
    "debtor_client": {
      "id": 1,
      "name": "Comercializadora del Norte",
      "archetype": "retail_chain"
    },
    "amount": "150000.00",
    "issue_date": "2026-08-15",
    "due_date": "2026-10-15",
    "status": "pending",
    "days_until_due": 33
  }
]
```

Currently returns 4 invoices, all `"status": "pending"`. `days_until_due`
is computed live from `due_date` vs. today, so it changes day to day even
though the rest of the fixture is static. `status` is one of `pending`,
`in_auction`, `funded`, `paid`, `overdue` (matches `Invoice.Status` in
`facturas/models.py`), though only `pending` shows up here for now.

---

## `POST /api/invoices/{id}/offers/`

Simulates running the bidding process for one invoice: returns 4 fake
offers from 4 different lenders with distinct pricing. Nothing is
persisted — calling this twice for the same invoice returns the same 4
offers.

**Request**: no body needed. `{id}` is the invoice's `id` from the list
above (currently `1`–`4`).

**Response**: `200 OK`, a JSON array of offer objects.

```json
[
  {
    "id": 101,
    "invoice_id": 1,
    "lender": {
      "id": 1,
      "name": "Financiera del Bajío",
      "risk_profile": "conservative"
    },
    "advance_percentage": "80.00",
    "rate": "2.10",
    "net_amount": "120000.00",
    "expires_at": "2026-09-13T18:04:22.104932+00:00"
  },
  {
    "id": 102,
    "invoice_id": 1,
    "lender": {
      "id": 2,
      "name": "Capital Ágil MX",
      "risk_profile": "aggressive"
    },
    "advance_percentage": "92.00",
    "rate": "4.50",
    "net_amount": "138000.00",
    "expires_at": "2026-09-13T18:04:22.104932+00:00"
  },
  {
    "id": 103,
    "invoice_id": 1,
    "lender": {
      "id": 3,
      "name": "Fondeo Azteca",
      "risk_profile": "moderate"
    },
    "advance_percentage": "87.00",
    "rate": "3.20",
    "net_amount": "130500.00",
    "expires_at": "2026-09-13T18:04:22.104932+00:00"
  },
  {
    "id": 104,
    "invoice_id": 1,
    "lender": {
      "id": 4,
      "name": "Nortem Capital",
      "risk_profile": "moderate"
    },
    "advance_percentage": "85.50",
    "rate": "2.85",
    "net_amount": "128250.00",
    "expires_at": "2026-09-13T18:04:22.104932+00:00"
  }
]
```

`net_amount` is computed from the invoice's real `amount` × that offer's
`advance_percentage` — it isn't hardcoded, so it stays consistent if you
change which invoice you're calling this on. `expires_at` is `now + 24h`,
computed at request time. `id` is deterministic (`invoice_id * 100 +
position`) purely so this fixture has stable, predictable ids — don't
rely on that formula once real offers exist.

**Error response**: `404 Not Found` if `{id}` doesn't match a known
invoice:

```json
{ "detail": "Invoice not found." }
```

---

## `POST /api/offers/{id}/accept/`

Simulates accepting one of the offers returned above. Always succeeds —
there's no real offer store yet, so any numeric `{id}` is accepted.

**Request**: no body needed. `{id}` is an offer's `id` from the offers
response above (e.g. `101`).

**Response**: `200 OK`.

```json
{
  "offer_id": 101,
  "invoice_id": 1,
  "status": "accepted",
  "transaction_id": "TXN-3F2A9C1B7E4D",
  "accepted_at": "2026-09-12T18:05:01.552341+00:00",
  "settlement_date": "2026-09-15"
}
```

`invoice_id` is derived from `offer_id` using the same `// 100` scheme
the offers endpoint used to generate the id — again, don't depend on
that once this is backed by real data. `transaction_id` and
`accepted_at` are freshly generated on every call, so calling this twice
with the same `offer_id` returns two different `transaction_id`s (there's
no idempotency yet).

---

## What changes when this becomes real

- `GET /api/invoices/` will filter by the authenticated company instead
  of returning one hardcoded company's invoices.
- `POST /api/invoices/{id}/offers/` will run actual lender
  matching/pricing instead of returning the same 4 fixed offers, and
  offers will be persisted (`mercado.Offer`) so `id`s are real primary
  keys, not `invoice_id * 100 + n`.
- `POST /api/offers/{id}/accept/` will look up a real `Offer`, reject
  unknown/expired/already-accepted ids with real error responses, and
  update the linked `Invoice.status` to `funded`.
- Field names and types are the target contract and are meant to stay
  stable through that transition — flag it early if a real
  implementation needs to change one.
