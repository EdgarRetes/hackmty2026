# Backend — factorai_config (Django + DRF)

API-only Django backend. No templates, no admin site, no static file
serving — every response is JSON. Deploys as a Docker container on Vultr.

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
- `production.py` — Docker/Vultr deployment. Requires `SECRET_KEY`,
  `ALLOWED_HOSTS`, `DATABASE_URL` to be set; no insecure fallbacks.

`manage.py` defaults to `factorai_config.settings.dev`. The Docker image
sets `DJANGO_SETTINGS_MODULE=factorai_config.settings.production`.

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

With no `DATABASE_URL` set, this uses local SQLite automatically.

Verify: `curl http://localhost:8000/api/health/` should return
`{"status": "ok", "service": "factorai-backend"}`.

## Running against local TimescaleDB via Docker

```bash
docker compose up --build
```

This starts a `timescale/timescaledb` container alongside the Django app
so local dev matches the production database (Postgres + TimescaleDB).

## Apps

- `empresas` — Mexican SMEs requesting financing
- `financiadoras` — lenders placing bids
- `facturas` — receivables/invoices put up for financing
- `mercado` — bids and auction outcomes
- `core` — shared utilities, health check endpoint

Each app currently has only a placeholder comment in `models.py` — no
real models yet.
