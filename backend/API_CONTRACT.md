# API Contract

**Status**: `GET /api/invoices/`, `GET /api/invoices/{reference}/`,
`GET|POST /api/invoices/{id}/offers/`, and `POST /api/offers/{id}/accept/` are
backed by real data — real seeded `Invoice` rows, a real quantile
risk model (`core/risk_engine.py`), three real `cvxpy` pricing agents
(`core/pricing_agents.py`), and a real matching engine
(`mercado/matching_engine.py`) that ranks their quotes. Generated offers
and their acceptance state are persisted. This document describes the exact shape the frontend
builds against; if a field ever needs to change, this file gets updated
in the same PR.

Base URL locally: `http://localhost:8000`. All request/response bodies
are JSON. Money fields (`amount`, `net_amount`, `advance_percentage`,
`rate`) are **strings**, not numbers — that's how DRF's `DecimalField`
serializes by default. Parse with a decimal-safe parser on the frontend,
not `parseFloat` if you can help it (floating point rounding on money).

**Before any of this returns real data, seed the database**:
`python manage.py seed_demo_data` (see `backend/README.md`).

---

## `GET /api/invoices/`

Returns the real list of pending invoices from the database (no
auth/company filtering yet — every seeded invoice belongs to the same
demo company).

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
      "archetype": "reliable"
    },
    "amount": "150000.00",
    "issue_date": "2026-08-15",
    "due_date": "2026-10-15",
    "status": "pending",
    "days_until_due": 33
  }
]
```

Returns however many pending invoices `seed_demo_data` created (8-15,
re-seeding changes both the count and the ids). `folio` is a
display-only label derived from the id (`FAC-2026-{id:04d}`) — the
`Invoice` model has no `folio` column. `debtor_client.archetype` is a
**payment-behavior** category (`reliable` / `irregular` / `delinquent` /
`new`), not an industry — don't confuse it with the industry "sector"
used internally by the specialized pricing agent, which isn't exposed
over the API. `days_until_due` is computed live from `due_date` vs.
today. `status` is one of `pending`, `in_auction`, `funded`, `paid`,
`overdue` (`Invoice.Status`), though only `pending` shows up here today.

---

## `GET /api/invoices/{reference}/`

Returns one invoice using its numeric database id, `INV-{id}`, or display
folio `FAC-2026-{id:04d}`. The response has the same shape as one item from
the invoice list. Unknown references return `404` with
`{"detail": "Invoice not found."}`.

---

## `GET|POST /api/invoices/{id}/offers/`

Runs the invoice through the real pipeline: `core.risk_engine.predict_risk`
produces a `{p10, p50, p90}` days-late band from that invoice's
`DebtorClient` payment history, all three pricing agents
(`conservative`, `aggressive`, `specialized`) price the invoice against
that band, and `mercado.matching_engine.rank_offers` sorts the three
resulting quotes by **net cash to the empresa** (`net_amount`,
descending — ties broken by the lower rate). Each quote is persisted or
updated for its `(invoice, lender)` pair.

`GET` returns already persisted offers without recalculating them. `POST`
generates or refreshes offers for a pending invoice. Funded invoices always
return their persisted offers without repricing.

**Request**: no body needed. `{id}` is a real invoice `id` from the list
above.

**Response**: `200 OK`, a JSON array of exactly 3 offer objects — one
per pricing agent — **already sorted best-for-the-empresa first**.

```json
[
  {
    "id": 103,
    "invoice_id": 1,
    "lender": {
      "id": 3,
      "name": "Fondeo Azteca",
      "risk_profile": "specialized"
    },
    "advance_percentage": "85.87",
    "rate": "2.63",
    "net_amount": "128805.00",
    "financing_cost": "3945.00",
    "funding_time": "24 horas",
    "category": "best",
    "rank": 1,
    "expires_at": "2026-09-13T18:04:22.104932+00:00",
    "is_accepted": false
  },
  {
    "id": 102,
    "invoice_id": 1,
    "lender": {
      "id": 2,
      "name": "Capital Ágil MX",
      "risk_profile": "aggressive"
    },
    "advance_percentage": "90.54",
    "rate": "3.38",
    "net_amount": "135810.00",
    "expires_at": "2026-09-13T18:04:22.104932+00:00"
  },
  {
    "id": 101,
    "invoice_id": 1,
    "lender": {
      "id": 1,
      "name": "Financiera del Bajío",
      "risk_profile": "conservative"
    },
    "advance_percentage": "72.14",
    "rate": "4.04",
    "net_amount": "108210.00",
    "expires_at": "2026-09-13T18:04:22.104932+00:00"
  }
]
```

(Real numbers vary invoice to invoice and after re-seeding — the example
above is illustrative, not fixed.) `expires_at` is `now + 24h`, computed
at request time. `id` is a real persisted `Offer` primary key.
`financing_cost` is calculated in the backend; `funding_time` belongs to
the lender profile; and `category` is `best`, `lowest_rate`,
`highest_advance`, or `fastest`.

**Array order is the ranking** — index 0 is the offer the matching
engine judges best for the empresa. Don't re-sort by `advance_percentage`
alone client-side; the engine already accounts for `rate` as a tiebreak.

**Error response**: `404 Not Found` if `{id}` doesn't match a real
invoice:

```json
{ "detail": "Invoice not found." }
```

---

## `POST /api/offers/{id}/accept/`

Accepts a persisted, unexpired offer, records its acceptance timestamp,
and updates its invoice status to `funded`.

**Request**: no body needed. `{id}` is an offer's `id` from the offers
response above (e.g. `103`).

**Response**: `200 OK`.

```json
{
  "offer_id": 103,
  "invoice_id": 1,
  "status": "accepted",
  "transaction_id": "TXN-3F2A9C1B7E4D",
  "accepted_at": "2026-09-12T18:05:01.552341+00:00",
  "settlement_date": "2026-09-15"
}
```

Unknown offers return `404`. Expired or already accepted offers return
`409`. A transaction identifier is generated for each successful acceptance.

---

## What changes when this becomes real

- `GET /api/invoices/` will filter by the authenticated company instead
  of returning every seeded invoice.
- Authentication and company-level authorization must be added before
  customer-specific production access.
- The specialized pricing agent's "sector" concept isn't backed by a
  real model field yet (see `core/demo_sectors.py`) — a real
  implementation should add it to `DebtorClient` (or a separate model)
  rather than a hardcoded name lookup.
- Field names and types are the target contract and are meant to stay
  stable through that transition — flag it early if a real
  implementation needs to change one.
