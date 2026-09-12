# Backend-specific agent notes

See the root [`/AGENTS.md`](../AGENTS.md) for project-wide context. This
file only covers Django-specific conventions for this `backend/` folder.

## Conventions

- **API-only, forever.** Never add `django.contrib.admin`, `TEMPLATES`,
  server-rendered views, or static file serving. Every response is JSON
  via DRF. If a feature seems to need a template, it belongs in the
  Next.js frontend instead.
- **Settings split.** Never put environment-specific values (secrets,
  hosts, DB config) in `base.py`. Add them to `dev.py` and
  `production.py` separately, read via `django-environ`.
- **All config via env vars.** No hardcoded secrets, hosts, or connection
  strings anywhere in the codebase. Add new env vars to `.env.example`
  and document them in `README.md`.
- **New apps** go at the repo root next to `empresas/`, `financiadoras/`,
  etc., created with `python manage.py startapp <name>` and registered in
  `factorai_config/settings/base.py` → `INSTALLED_APPS`.
- **New endpoints**: add a view in the relevant app's `views.py`, wire it
  into that app's `urls.py`, and include that app's urls from
  `factorai_config/urls.py` under an `/api/<app>/` prefix (see
  `core/urls.py` for the pattern).
- **New models** go in the relevant app's `models.py`, replacing the
  placeholder comment, followed by `python manage.py makemigrations`.
- **Tiger Cloud / TimescaleDB**: when you eventually create a
  hypertable, use the modern declarative syntax
  (`CREATE TABLE ... WITH (tsdb.hypertable = true, tsdb.partition_column = '...')`)
  — not the legacy `create_hypertable()` function. Check current Tiger
  Data docs first, since this has changed across TimescaleDB versions.
  See the comment in `core/models.py`.
- Remember the **DB_PASSWORD override** for Tiger Cloud connections — see
  `README.md`.

## Non-goals right now

No auth/permissions, no real models, no business logic. This is
skeleton-only scaffolding to prove the stack runs end-to-end.
