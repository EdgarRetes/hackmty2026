# Backend — factorai_config (Django + DRF)

API-only Django backend. No templates, no admin site, no static file
serving — every response is JSON. Deploys directly onto a plain Ubuntu
VPS (no containers) via Gunicorn + systemd + Nginx — see `DEPLOY.md`.

## Stack

- Django 6.1.1
- Django REST Framework 3.18.1
- django-environ + dj-database-url for env-based config
- psycopg 3 (`psycopg[binary]`) as the Postgres driver — **not** psycopg2
- django-cors-headers
- Gunicorn (production WSGI server)

## Settings layout

`factorai_config/settings/` is split into:

- `base.py` — shared apps, middleware, everything environment-agnostic
- `dev.py` — local development. Falls back to SQLite if `DATABASE_URL`
  isn't set, so the project runs with zero external services.
- `production.py` — VPS deployment. Requires `SECRET_KEY`,
  `ALLOWED_HOSTS`, `DATABASE_URL` to be set; no insecure fallbacks.

`manage.py` defaults to `factorai_config.settings.dev`. In production,
`DJANGO_SETTINGS_MODULE=factorai_config.settings.production` is set via
the server's `.env` file (see `DEPLOY.md`).

## ⚠️ Tiger Cloud password gotcha — read this before debugging an auth failure

Tiger Cloud's connection string for a service does **not** include the
database password — it's shown to you once, separately, and must be
supplied out of band. If you paste the connection string straight into
`DATABASE_URL` and nothing else, Postgres auth will fail even though the
URL looks complete.

This project handles it explicitly: set the connection string (password
omitted or with a placeholder) as `DATABASE_URL`, and put the real
password in a separate `DB_PASSWORD` env var. Both `dev.py` and
`production.py` parse `DATABASE_URL` with `dj_database_url`, then — if
`DB_PASSWORD` is present — overwrite the parsed password with it before
`DATABASES` is finalized. If you ever see authentication failures against
Tiger Cloud, check `DB_PASSWORD` first.

## Environment variables

See `.env.example`. Copy it to `.env` and load it into your shell (or a
tool like `direnv`/`python-dotenv`) before running `manage.py`.

| Var | Purpose |
|---|---|
| `DATABASE_URL` | Postgres connection string (password may be omitted — see above) |
| `DB_PASSWORD` | Overrides/fills the password from `DATABASE_URL`. Required for Tiger Cloud. |
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True`/`False` |
| `ALLOWED_HOSTS` | Comma-separated |
| `CORS_ALLOWED_ORIGINS` | Comma-separated, must include the frontend's origin |
| `GEMINI_API_KEY` | Not used yet — reserved for later Gemini API integration |

## Running locally

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

With no `DATABASE_URL` set, this uses local SQLite automatically — no
local database setup required at all.

If you want to develop against the real schema (e.g. to test
TimescaleDB-specific behavior), set `DATABASE_URL` (and `DB_PASSWORD` —
see the gotcha above) in your `.env` to point directly at the Tiger
Cloud Postgres instance instead of SQLite. There is no local
containerized database — dev is either SQLite or the real Tiger Cloud
service.

Verify: `curl http://localhost:8000/api/health/` should return
`{"status": "ok", "service": "factorai-backend"}`.

## Deploying

See `DEPLOY.md` for the exact commands to run on the Ubuntu VPS
(Gunicorn + systemd + Nginx, no Docker).

## Apps

- `empresas` — Mexican SMEs requesting financing
- `financiadoras` — lenders placing bids
- `facturas` — receivables/invoices put up for financing
- `mercado` — bids and auction outcomes
- `core` — shared utilities, health check endpoint

`empresas`, `financiadoras`, `facturas`, and `mercado` have real models
(`Company`/`DebtorClient`/`PaymentHistory`, `Lender`, `Invoice`, `Offer`
respectively), each registered in that app's `admin.py`. `/admin/` is
enabled as an internal data-management UI — create a superuser with
`python manage.py createsuperuser` to use it. Invoice underwriting and
offer matching are implemented as the explainable hackathon MVP below.

## Explainable risk MVP

### Design decision

The production path uses a deterministic scorecard instead of fitting a
machine-learning model to synthetic data. A scorecard is reproducible, explains
every decision and gives tests stable expected outcomes. The previous quantile
experiment no longer controls approval; `predict_risk()` remains only as a
compatibility view of contractual days past due.

The engine has two gates:

1. **Eligibility** validates the asset: current SAT status, PPD payment method,
   issuer/receiver RFC match, positive outstanding balance, future due date,
   delivery evidence, no dispute, no prior assignment and no duplicate UUID or
   XML hash.
2. **Credit assessment** scores payment behavior (40%), payer strength (25%),
   invoice characteristics (20%) and payer concentration (15%). Missing history
   or financial indicators returns `REVIEW`; excessive risk returns `REJECT`;
   only `APPROVE` can create offers.

The 0–100 score maps to explicit A–E bands, demo PD, LGD and advance policy in
`core/risk_policy.py`. Those bands are prototype assumptions, not statistically
calibrated or CNBV-approved values.

### Loss and price formulas

All rates are decimal fractions inside Python and persisted snapshots:

```text
EAD = outstanding_balance × advance_percentage
expected_default_loss = PD × LGD × EAD
expected_dilution_loss = seller_dilution_rate × EAD
expected_loss = expected_default_loss + expected_dilution_loss

annual_rate = TIIE_funding + operating_spread + capital_margin
              + min(annualized_expected_loss_spread, 30%)
period_cost = EAD × ((1 + annual_rate)^(term_days / 360) - 1)
monthly_rate = (1 + annual_rate)^(1 / 12) - 1
net_disbursement = EAD - period_cost
expected_investor_profit = period_cost - expected_loss - reference_funding_cost
```

The pricing snapshot uses Banco de México's 6.49% annual TIIE de Fondeo
observation dated 2026-09-11. Its date and URL are persisted so an old assessment
never changes when rates move. A production adapter would ingest and approve new
SIE snapshots before changing policy.

### Official data grounding

Seeded entities are fictional. “Official-shaped” means fields and definitions
match authoritative sources, not that the fictional values were returned by
those services:

- [SAT individual CFDI verification](https://wwwmat.sat.gob.mx/aplicacion/80523/verifica-tus-facturas-electronicas): UUID, issuer RFC, receiver RFC and current/cancelled status. Individual validation does not require authentication.
- [SAT consultation and recovery](https://wwwmatnp.sat.gob.mx/consultas/42968/consulta-y-recuperacion-de-comprobantes-%28nuevo%29): authenticated XML/metadata retrieval and cancellation metadata. This future adapter requires Contraseña/e.firma.
- [Banco de México SIE](https://www.banxico.org.mx/SieInternet/consultarDirectorioInternetAction.do?accion=consultarCuadro&idCuadro=CF111): dated TIIE reference rate.
- [INEGI DENUE API](https://www.inegi.org.mx/servicios/api_denue.html): SCIAN activity, establishment size, location and identification metadata.
- [Basel CRE30](https://www.bis.org/basel_framework/chapter/CRE/30.htm?inforce=20230101&published=20200327&tldate=20230123) and [CRE34](https://www.bis.org/basel_framework/chapter/CRE/34.htm?inforce=20230101&published=20201126&tldate=20191003): PD, LGD, EAD, maturity and separate purchased-receivable dilution risk.
- [Basel CRE36](https://www.bis.org/basel_framework/chapter/CRE/36.htm?inforce=20230101&published=20221208&tldate=20090325): ageing, documents, concentration, dilution and seller/obligor monitoring.
- [IFRS 9](https://www.ifrs.org/content/dam/ifrs/publications/pdf-standards/english/2022/issued/part-a/ifrs-9-financial-instruments.pdf?bypass=on): probability-weighted expected loss, time value and reasonable historical/current/forward-looking information.

Mock company and payer rows include `data_source`, `source_reference` and
`data_as_of`; every `RiskAssessment` stores its input snapshot, policy version
and reference-rate snapshot. Never label the demo as a live SAT, DENUE or bureau
check.

### Payment semantics

Payment history stores issue, contractual due and actual paid dates.
`days_past_due = max(paid_at - due_at, 0)`. The former demo treated a normal
30-day invoice term as 30 days late, reversing the target's meaning.

### API behavior

```text
POST /api/invoices/{id}/risk-assessment/  create immutable assessment
GET  /api/invoices/{id}/risk-assessment/  latest assessment
POST /api/invoices/{id}/offers/           assess, reject with 422, or price offers
```

Approved lender variants adjust advance and annual spread around the central
recommendation, then rank by cash delivered after the full term cost. Persisted
offers reference the exact assessment used.

### Production evolution

Replace snapshots through provider interfaces rather than changing scorecard
callers: SAT XML/status, consented bureau, DENUE and bank/cash-flow providers.
Recalibrate PD only after labeled outcomes, temporal validation, probability
calibration, drift monitoring and model governance. KYC/KYB and lender
suitability remain separate onboarding gates.

Selecting invoices against a liquidity target is the next phase: binary
MILP/CP-SAT constrained by eligibility, net disbursement, payer/sector
concentration, lender capital and expected loss. `InvoiceBatch` remains manual.
