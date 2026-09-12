# factorai (mty2026)

A monorepo skeleton for a factoring marketplace where multiple
**financiadoras** (lenders) compete by bidding on pending invoices from
Mexican SMEs. This is scaffolding only — no business logic yet. See
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
| Deploy | Docker container on **Vultr** | **Vercel** |

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
