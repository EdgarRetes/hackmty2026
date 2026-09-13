# API Contract

**Status**: `GET /api/invoices/`, `GET /api/invoices/{reference}/`,
`GET|POST /api/invoices/{id}/offers/`, and `POST /api/offers/{id}/accept/` are
backed by real data — seeded `Invoice` rows, an explainable eligibility and
credit scorecard (`core/risk_engine.py`), term-sensitive lender policies, and a
matching engine (`mercado/matching_engine.py`) that ranks cash after cost. Generated offers
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

## `GET|POST /api/invoices/{id}/risk-assessment/`

`POST` runs eligibility, the scorecard and term-sensitive pricing, then
persists an immutable snapshot (`201`). `GET` returns the latest snapshot
(`404` before the first evaluation).

Core fields include `decision`, `rating`, `risk_score`,
`probability_of_default`, `loss_given_default`, `exposure_at_default`,
`expected_loss`, `term_days`, `recommended_monthly_rate`, `financing_cost`,
`net_disbursement`, `expected_investor_profit`, `reasons`, `warnings`,
`policy_version` and the dated reference-rate source. PD, LGD and rates are
decimal fractions; money and decimals serialize as strings.

Only `APPROVE` proceeds automatically. `REVIEW` means insufficient evidence;
`REJECT` means an eligibility rule or maximum risk band failed.

---

## `GET /api/invoices/`

Returns the real list of invoices from the database (no
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
    "days_until_due": 33,
    "offers_count": 3
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
`overdue` (`Invoice.Status`). `offers_count` is the real count of persisted
offers related to the invoice.

---

## `GET /api/invoices/{reference}/`

Returns one invoice using its numeric database id, `INV-{id}`, or display
folio `FAC-2026-{id:04d}`. The response has the same shape as one item from
the invoice list. Unknown references return `404` with
`{"detail": "Invoice not found."}`.

---

## `GET|POST /api/invoices/{id}/offers/`

Runs eligibility and credit assessment first. Approved invoices are priced by
three lender policies around the assessment's recommended advance and annual
rate; `mercado.matching_engine.rank_offers` sorts by cash delivered after the
full term cost. Each quote is persisted or updated for its `(invoice, lender)`
pair.

`GET` returns already persisted offers without recalculating them. `POST`
generates or refreshes offers for a pending invoice. Funded invoices always
return their persisted offers without repricing.

A non-approved invoice returns `422` with
`{"detail": "Invoice did not pass automatic underwriting.", "assessment": {...}}`
and removes stale offers. Approved offers store `risk_assessment_id`; `rate` is
the effective monthly percentage, `financing_cost` covers the remaining term,
and `net_amount` is cash after that cost.

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
    "is_accepted": false,
    "accepted_at": null
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
`highest_advance`, or `fastest`. `accepted_at` is `null` until the offer
is accepted and then contains the persisted acceptance timestamp.

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

## `GET|POST /api/invoice-batches/`

A "publicación": several of the empresa's own **pending, unbatched**
invoices published together as one package. A financiadora funding the
batch pays out all its invoices at once and collects the yield across
all of them — this is the multi-invoice equivalent of the single-invoice
flow above.

**`POST`** body: `{"invoice_ids": [87, 97, 96]}` — at least 2 ids,
all must currently be `status: "pending"`, not already in another
batch, and belong to the same company. Publishing flips each invoice's
`status` to `in_auction` and sets its `batch_id`.

**Response** (`201` on POST, `200` on GET — a list of these):

```json
{
  "id": 1,
  "company": { "id": 1, "legal_name": "...", "rfc": "..." },
  "invoices": [ /* same shape as GET /api/invoices/ items, each now with batch_id: 1 */ ],
  "total_amount": "626748.29",
  "created_at": "2026-09-12T16:55:28.794211-06:00"
}
```

`400` if fewer than 2 ids, an id doesn't exist/isn't pending/is already
batched, or the invoices span more than one company.

## `GET /api/invoice-batches/{id}/`

One batch, same shape as a `POST` response above. `404` if unknown.

## `GET /api/invoice-batches/{id}/offers/`

Runs the **exact same** per-invoice pipeline (risk engine → 3 pricing
agents → matching engine) on every invoice in the batch, then combines
each lender's quotes across all of them into one package-level offer:
`net_amount` summed, `rate`/`advance_percentage` amount-weighted-averaged
across the batch's invoices. Same per-offer shape as
`/api/invoices/{id}/offers/` plus `batch_id` instead of `invoice_id` —
**computed on every call, not persisted** (unlike single-invoice offers).

**No accept endpoint yet for batch offers.** Their `id` is synthetic
(`batch_id * 100 + rank`, same scheme the single-invoice endpoint used
before it persisted real `Offer` rows) and does **not** correspond to a
real `Offer` primary key — don't call `POST /api/offers/{id}/accept/`
with one, since it could collide with an unrelated real `Offer`'s id.
Accepting a batch offer (funding all its invoices at once) isn't
implemented yet.

---

## What changes when this becomes real

- `GET /api/invoices/` will filter by the authenticated company instead
  of returning every seeded invoice.
- Authentication and company-level authorization must be added before
  customer-specific production access.
- `DebtorClient.scian_sector` is currently a deterministic DENUE-shaped mock;
  production must populate and refresh it through an approved provider.
- Field names and types are the target contract and are meant to stay
  stable through that transition — flag it early if a real
  implementation needs to change one.
