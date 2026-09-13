# factorai (mty2026)

A working hackathon MVP for a factoring marketplace where multiple
**financiadoras** (lenders) compete by bidding on pending invoices from
Mexican SMEs. It includes explainable invoice underwriting, term-sensitive
pricing, deterministic approval/review/rejection demos and persisted offers. See
[`AGENTS.md`](AGENTS.md) for the full project brief and conventions.

## Layout

```
/backend    Django + DRF, API-only
/frontend   Next.js (App Router)
```

## Stack & deploy targets

| | Backend | Frontend |
|---|---|---|
| Framework | Django 6.1 + DRF 3.18 | Next.js 16 (App Router) |
| Language | Python | TypeScript |
| Database | PostgreSQL + TimescaleDB (Tiger Cloud) | — |
| Deploy | Plain Ubuntu VPS on **Vultr** (Gunicorn + systemd + Nginx, no Docker) | **Vercel** |

## Quickstart

**Backend** (see [`backend/README.md`](backend/README.md) for details):

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

**Frontend**:

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

With both running, open http://localhost:3000 — it calls the backend's
`GET /api/health/` and displays the JSON response on screen. That round
trip is the proof the two services are wired together correctly.

## MVP de riesgo

`python manage.py seed_demo_data` creates four deterministic scenarios:

| Scenario | Expected decision | Purpose |
|---|---|---|
| `approved` | `APPROVE` / A | Valid CFDI-shaped fields and a strong payer |
| `risk_rejected` | `REJECT` / E | Severe arrears, defaults and weak payer indicators |
| `eligibility_rejected` | `REJECT` | Cancelled CFDI status |
| `manual_review` | `REVIEW` / N | Insufficient payment history and bureau information |

The offers page displays PD, LGD, expected loss, score, rating, term,
suggested monthly rate, reasons and warnings. Values are fictional and
deterministic: they demonstrate the contract and policy, not a regulated rating
or a live SAT/bureau response. Design decisions, formulas, official references
and limitations are documented in
[`backend/README.md`](backend/README.md#explainable-risk-mvp).
