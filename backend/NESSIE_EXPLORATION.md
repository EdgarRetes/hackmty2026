# Nessie API Exploration (Phase 1)

**Status: exploration only. Nothing in this document required writing to
our database or to Nessie.** All calls below were `GET` (or a `GET` to a
deliberately-fake id, to check error shape) against the live API using
the key stored in `backend/.env` as `NESSIE_API_KEY` — never printed,
never hardcoded, never committed.

## How the docs were actually read

`https://prod.nessieisreal.com/` is a React SPA — its HTML ships almost
nothing (`<div id="root">`), so a plain fetch/scrape returns just the
page title. The real API host is `https://prod-api.nessieisreal.com`
(found in the SPA's JS bundle). That host serves its own live OpenAPI
spec at **`GET /openapi`** (no auth required) — a ~74KB YAML document,
version `1.0.0`. That spec is what's summarized below, then every `GET`
path in it (plus a couple the spec doesn't mention — see below) was
actually called.

**Auth mechanism, confirmed**: the key goes as a **query parameter**,
`?key=<key>`, on every single request — not a header. This matches the
spec's `ApiKeyAuth` security scheme (`type: apiKey, in: query, name: key`).

## The documented endpoint inventory

| Resource | Regular-scope paths | Enterprise-scope paths |
|---|---|---|
| Customers | `GET/POST /customers`, `GET/PUT /customers/{id}`, `GET/POST /customers/{id}/accounts`, `GET /customers/{id}/bills`, `GET /accounts/{id}/customer` | `GET /enterprise/customers`, `GET /enterprise/customers/{id}` |
| Accounts | `GET/PUT/DELETE /accounts/{id}`, `GET /accounts` | **none documented** |
| Bills | `GET/POST /accounts/{id}/bills`, `GET/PUT/DELETE /bills/{billId}` | none |
| Deposits | `GET/POST /accounts/{id}/deposits`, `GET /deposits`, `GET/PUT/DELETE /deposits/{id}` | `GET /enterprise/deposits`, `GET /enterprise/deposits/{id}` |
| Withdrawals | `GET/POST /accounts/{id}/withdrawals`, `GET/PUT/DELETE /withdrawal/{id}` | `GET /enterprise/withdrawal/{id}` (**no list**) |
| Loans | `GET/POST /accounts/{id}/loans`, `GET/PUT/DELETE /loans/{id}` | none |
| Merchants | `GET/POST /merchants`, `GET/PUT /merchants/{id}` | none |
| ATMs | `GET /atms`, `GET /atms/{id}` | none |
| Branches | `GET /branches`, `GET /branches/{id}` | none |
| Purchases | `GET/PUT/DELETE /purchase/{id}` (**no list, no POST at all**) | none |
| Transfers | `GET/PUT/DELETE /transfers/{id}` (**no list, no POST at all**) | none |

**Important gap in the spec itself**: there is no documented way to
*create* a purchase or a transfer (no `POST` for either), and no way to
*list* purchases or transfers for an account or customer via any
documented path.

## What's actually true that the docs don't say

Two endpoints work perfectly and return real data despite **not
appearing anywhere in the live OpenAPI spec**:

- **`GET /enterprise/accounts`** — 200, 529 records. Not in the spec's
  `Enterprise` tag at all (which only lists customers/deposits/withdrawal).
- **`GET /accounts/{id}/purchases`** — 200, real records with `payer_id`
  and `merchant_id` linkage. Not in the spec's `Purchases` tag (which
  only has singular `/purchase/{id}`).

This is exactly the kind of drift the task asked me to check for instead
of assuming — the interactive docs are stale relative to what's deployed.

## Endpoint-by-endpoint results

### Regular (key-scoped) endpoints

| Endpoint | Status | Result |
|---|---|---|
| `GET /customers` | 200 | `[]` — empty |
| `GET /accounts` | 200 | `[]` — empty |
| `GET /merchants` | 200 | `[]` — empty |
| `GET /deposits` | 200 | `[]` — empty |
| `GET /atms` | 200 | **13 records**, real (see below) |
| `GET /branches` | 200 | **207 records**, real (see below) |
| `GET /customers/{id}/accounts` (foreign id) | 200 | `[]` |
| `GET /customers/{id}/bills` (foreign id) | 200 | `[]` |
| `GET /accounts/{id}` (foreign, enterprise-owned id) | **404** | `"Account with this id does not exist"` — correctly ownership-scoped |
| `GET /accounts/{id}/customer` (same foreign id) | **404** | `"Account with this id does not exist"` — correctly scoped |
| `GET /accounts/{id}/deposits` (same foreign id) | 200 | `[]` — **not** ownership-checked, just returns nothing |
| `GET /accounts/{id}/withdrawals` (same foreign id) | 200 | `[]` |
| `GET /accounts/{id}/bills` (same foreign id) | 200 | `[]` |
| `GET /accounts/{id}/loans` (same foreign id) | 200 | `[]` |
| `GET /accounts/{id}/transfers` (same foreign id) | **404** | `"No transfers found for this account"` |
| `GET /accounts/{id}/purchases` (foreign, undocumented) | 200 | **real data**, see below |
| `GET /merchants/{id}` (a real id referenced by a purchase) | **404** | `"Merchant id does not exist"` — correctly scoped, invisible across keys |
| `GET /withdrawal/{fake_id}` | 404 | `"Withdrawal with this id does not exist"` |
| `GET /purchase/{fake_id}` | 404 | `"Purchase with this id does not exist"` |
| `GET /transfers/{fake_id}` | 404 | `"Transfer not found"` |

`atms` and `branches` behave like shared static reference data (real,
non-trivial, not obviously key-scoped) — a sample ATM: `{"name": "Arlington 1", "language_list": ["Portuguese", "English"], "geocode": {"lat": 38.898, "lng": -77.121}, ...}`; a sample branch:
`{"_id": "56c66be5a73e4927415071a3", "name": "ARLINGTON", "phone_number": "(703) 812-8550", ...}`.

### Enterprise-scope endpoints

| Endpoint | Status | Result |
|---|---|---|
| `GET /enterprise/customers` | 200 | **227 records** |
| `GET /enterprise/accounts` (undocumented) | 200 | **529 records** |
| `GET /enterprise/deposits` | 200 | **3,910 records** |
| `GET /enterprise/customers/{real_id}` | 200 | full record, matches list shape |
| `GET /enterprise/deposits/{real_id}` | 200 | full record, matches list shape |
| `GET /enterprise/withdrawal/{fake_id}` | 404 | `"Withdrawal with this id does not exist"` (no list endpoint exists to find a real id) |

Sample enterprise customer:
```json
{
  "_id": "2c704dcb-a3e0-4642-81b5-51b5f51819e7",
  "first_name": "Rosa",
  "last_name": "Martínez",
  "address": {"street_number": null, "street_name": "Av. Constitución", "city": "Monterrey", "state": "NL", "zip": "64000"},
  "account_ids": []
}
```

Sample enterprise account:
```json
{
  "_id": "ee57daa0-ff9b-45f0-b5a6-f33c238eb816",
  "type": "Checking", "nickname": "Cuenta Rosa", "rewards": 0, "balance": 5000,
  "account_number": "1881129373311938", "customer_id": "b25c5e57-ec92-4360-b624-b1e24bcf5615"
}
```

Sample enterprise deposit:
```json
{"_id": "02e8d99d-a7c0-46fb-a621-953ad8ddaad8", "medium": "balance", "transaction_date": "2026-09-09", "status": "completed", "amount": 320, "description": "Sample campus paycheck"}
```

Sample purchase (from the undocumented `accounts/{id}/purchases`):
```json
{"_id": "fe214382-8988-471d-8f18-b9dae266e655", "type": "merchant", "merchant_id": "8a4a9661-...", "payer_id": "ee57daa0-...", "purchase_date": "2026-09-12", "amount": 125, "status": "completed", "medium": "balance", "description": null}
```

Note the `_id` values are UUIDs (36 chars), not the 24-char Mongo
ObjectIds the spec's schema declares (`minLength: 24, maxLength: 24`) —
another spec/reality mismatch, harmless for us since we just treat them
as opaque strings.

## Is enterprise data actually rich and usable? (the key question)

**Populated: yes. Usable for what the prompt wants: no**, for four
concrete, verified reasons:

1. **Heavy duplication / templating.** Of 227 enterprise customers, only
   130 distinct (first, last) name pairs exist. "Rosa Martínez" /
   Monterrey, NL appears 3+ times with identical or near-identical
   addresses. The deposit `"Sample campus paycheck"` for exactly `$320`
   appears dozens of times across only two transaction dates
   (2026-09-09, 2026-09-12) in a 3,910-record set. This isn't organic
   transaction history — it's bulk-generated or copy-pasted test data.

2. **Cross-team contamination.** Names/cities in the enterprise pool
   include `Estudiante Test`, `Testville`, `Scurry`/`Trip crew`, and
   literal Swagger placeholder values (`"status": "string"`,
   `"medium": "string"` on 8 deposits) — this is clearly a shared sandbox
   that every hackathon team's own experimentation writes into, not a
   curated dataset for us.

3. **No reliable join from deposits to a customer or account.** The
   `Deposit` schema has no `account_id` or `customer_id` field, in
   either scope — confirmed by inspecting both the list and the
   singular-by-id response. There is no way to answer "which customer
   made this deposit" through this API at all. This alone rules out
   "map enterprise transaction history onto archetypes" for deposits.

4. **Inconsistent, leaky scoping on sub-resources.** `accounts/{id}`
   and `accounts/{id}/customer` correctly 404 for an account our key
   doesn't own. But `accounts/{id}/deposits`, `/withdrawals`, `/bills`,
   `/loans` for that same foreign id return `200 []` instead of an
   error — and `accounts/{id}/purchases` for a foreign id actually
   returns real data belonging to another key's account. That's
   inconsistent enough that we can't trust it as a stable integration
   surface; it may well change under us.

`accounts/{id}/purchases` was the one genuinely promising find — it
does link to `payer_id` (account) and `merchant_id`. A 10-account sample
showed 7/10 had at least one purchase, but several returned
byte-for-byte identical response sizes (617 bytes) suggesting templated,
not organically distinct, purchase patterns per account.

## Recommendation

**Treat the sandbox as effectively empty for our purposes** — not
because it has zero records, but because none of the rich enterprise
data can be reliably attributed to a specific customer/account in a way
we could map onto our `reliable`/`irregular`/`delinquent`/`new`
archetypes, and what little is well-linked (`accounts/{id}/purchases`)
is templated and shared with every other team using this key pool.

Concretely, for Phase 2: **create our own Nessie customers and accounts**
for our demo `Company` and each `Lender` (fully under our control, so
we know exactly what's in them), store the returned `_id`s as new
`nessie_customer_id` / `nessie_account_id` fields via a migration, and
optionally use Nessie deposits (the one write endpoint that's simple and
well-documented) to give the demo some real-API money-movement flavor.

**`Invoice` stays entirely our own model** — Nessie has no invoice or
factoring concept, exactly as already decided. **`PaymentHistory`'s
archetype-driven distributions stay the actual signal for the risk
engine** — nothing here changes that; Nessie only adds surface realism
(real external ids, a couple of real deposits we create ourselves), not
new statistical signal.

## One thing to confirm before Phase 2

The prompt referenced `CLAUDE.md` (for model context) and a "Pendientes
conocidos" section to update. Neither exists anywhere in this repo —
only `frontend/CLAUDE.md`, which is a one-line auto-generated pointer to
`AGENTS.md` (all our actual docs, in English, live in `AGENTS.md` files).
Before I touch step 4 of Phase 2's verification, let me know: create a
new root `CLAUDE.md` with a "Pendientes conocidos" section, or add an
equivalent "Known pending items" section to the existing `AGENTS.md`
instead?
