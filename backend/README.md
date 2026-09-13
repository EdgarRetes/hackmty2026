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
| `GEMINI_API_KEY` | Gemini API key for the invoice-publishing assistant (`facturas/assistant.py`). Never hardcode, log, or commit it. |
| `GEMINI_MODEL` | Optional. Overrides the assistant's model (default `gemini-3.7-flash`). |
| `NESSIE_API_KEY` | Capital One Nessie sandbox key, used only by `manage.py seed_demo_data --with-nessie` to provision fake bank customers/accounts/deposits. Never hardcode, log, or commit it. |

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

## Arquitectura

Todo el flujo de negocio pasa por tres subsistemas, cada uno con una sola
responsabilidad, para que ninguno tenga que "adivinar" lo que hace otro:

```
                        ┌────────────────────────┐
                        │   core.risk_engine       │
                        │   evaluate_invoice() /   │
                        │   assess_invoice()       │  ← underwriting explicable
                        │   (elegibilidad + score) │     (una sola fuente de verdad)
                        └───────────┬──────────────┘
                                    │ RiskAssessment (persistido, inmutable)
                    ┌───────────────┼────────────────────┐
                    ▼               ▼                     ▼
        mercado.matching_engine   facturas.package_optimizer   facturas.assistant
        (cotiza 3 financiadoras   (arma el paquete óptimo      (agente Gemini con
         variando anticipo/tasa    para una meta de liquidez     function calling sobre
         alrededor de lo que        — usado por "Crear paquete") los mismos servicios)
         recomienda el underwriting)
```

- **`core.risk_engine`** es la única función que decide si una factura es
  financiable y a qué tasa. Todo lo demás (ofertas, paquetes, el asistente)
  consume su resultado — nunca vuelve a calcular riesgo por su cuenta.
- **`mercado.matching_engine`** simula 3 "personalidades" de financiadora
  (conservadora, agresiva, especializada) ofreciendo variantes de anticipo/tasa
  alrededor de la recomendación del underwriting, y las rankea por efectivo
  neto entregado a la empresa.
- **`facturas.package_optimizer`** resuelve, dado un monto objetivo de
  liquidez y un plazo (30/60/90 días), qué subconjunto de facturas elegibles
  lo cubre con la menor pérdida esperada (fuerza bruta sobre el espacio de
  subconjuntos — ver la nota de escalabilidad en la tabla de decisiones).
- **`facturas.services`** centraliza las reglas de publicar un paquete
  (`publish_invoices`) y de armar candidatos para el optimizador
  (`build_liquidity_candidates`), para que el endpoint REST y el asistente de
  IA nunca diverjan en la validación.
- **`facturas.assistant`** es un agente Gemini con *function calling* sobre
  esos mismos servicios: puede listar facturas, explicar por qué una no
  calificó, simular un paquete, optimizarlo por meta de liquidez, y — si el
  usuario lo confirma — publicarlo de verdad. Nunca inventa números: cada
  respuesta viene de una llamada real a estas funciones contra la base de
  datos en producción.

### Flujo de una publicación

1. La empresa ve sus facturas `available` (o le pide al asistente una
   combinación por monto objetivo).
2. `POST /api/invoice-batches/` (o la herramienta `publicar_paquete` del
   asistente) llama a `publish_invoices()`, que valida elegibilidad y crea un
   `InvoiceBatch` con su `factoring_term_days`.
3. Una financiadora consulta `GET /api/invoice-batches/{id}/offers/`, que
   corre el underwriting + matching engine sobre cada factura del paquete y
   agrega las 3 cotizaciones ponderadas por monto.
4. `POST /api/invoice-batches/{id}/accept/` persiste un `Offer` real por
   factura y marca todo el paquete como `in_auction` → `funded`.

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

Selecting invoices against a liquidity target now exists (`facturas/package_optimizer.py`,
used by `POST /api/invoice-batches/preview/` and the assistant's
`optimizar_paquete_por_liquidez` tool), but it's a brute-force 0/1 knapsack
over the candidate list, not a constrained solver — see the decisions table
below for why that's fine at hackathon scale and what a real deployment would
need instead (payer/sector concentration limits, lender capital constraints,
MILP/CP-SAT for larger candidate pools).

## Decisiones técnicas: qué usamos, por qué, y si serviría en producción

| Pieza | Qué usamos | Por qué lo elegimos | Ventaja sobre otras opciones | ¿Sirve en producción? |
|---|---|---|---|---|
| **Framework web** | Django + Django REST Framework | Es el framework con más baterías incluidas para modelar entidades financieras relacionadas (empresa → factura → oferta) con validación, migraciones y un ORM maduro desde el día uno de un hackathon. DRF da serializers, permisos y un exception handler consistentes gratis. | Frente a Flask/FastAPI: no tuvimos que armar ORM, migraciones ni admin a mano — eso costó tiempo cero. Frente a Node/Express: el ORM de Django modela mejor relaciones complejas (FKs, constraints a nivel de base de datos) sin un ORM externo. | **Sí**, con trabajo adicional real: reemplazar el servidor de desarrollo por Gunicorn/uWSGI detrás de Nginx (ya lo hacemos), agregar autenticación real (DRF SimpleJWT u OAuth), rate limiting, y logging estructurado. Django es un framework de producción probado (Instagram, Disqus) — no es una limitante. |
| **Base de datos** | PostgreSQL + TimescaleDB, hosteada en Tiger Cloud | Postgres da integridad transaccional real (constraints `CheckConstraint`, FKs) que un producto financiero necesita — no queríamos "facturas con monto negativo" siendo posible a nivel de base de datos. TimescaleDB extiende Postgres para series de tiempo (historial de pagos, tasas de referencia por fecha) sin cambiar de motor. | Frente a MongoDB/NoSQL: las relaciones factura↔empresa↔financiadora↔oferta son inherentemente relacionales; forzarlas a documentos hubiera significado reimplementar joins e integridad referencial a mano. Frente a MySQL: mejor soporte de tipos (JSONField nativo para `reasons`/`warnings`/`input_snapshot`) y extensiones (Timescale). | **Sí.** Postgres gestionado (Tiger Cloud, RDS, Cloud SQL) es una elección de producción estándar en fintech. Lo que faltaría: backups verificados, réplicas de lectura, y point-in-time recovery configurado explícitamente (Tiger Cloud lo ofrece, pero no lo activamos para el demo). |
| **Motor de riesgo** | Scorecard determinístico explicable (`core/risk_engine.py`), no machine learning | Empezamos con un modelo de regresión cuantil (`GradientBoostingRegressor` de scikit-learn) entrenado sobre datos sintéticos — pero un modelo de ML entrenado con datos inventados no aprende nada real, solo memoriza el ruido con el que lo generamos. Un scorecard es reproducible, cada decisión se explica con razones concretas, y las pruebas tienen resultados esperados estables. | Frente a un modelo de ML "real": no necesita datos históricos reales (que no existen para un demo), es auditable línea por línea (un regulador puede leer la fórmula), y no tiene el riesgo de overfitting a datos falsos que un ML sí tiene. | **Parcialmente.** El *framework* de dos compuertas (elegibilidad + score ponderado) sí es una arquitectura válida de producción — así funcionan muchos scorecards de crédito reales. Lo que **no** serviría tal cual: las bandas de PD/LGD/tasa están calibradas a mano, no con datos históricos reales, y necesitarían recalibración con outcomes reales, validación temporal y gobernanza de modelo antes de tomar decisiones de crédito reales (ver "Production evolution" arriba). |
| **Optimizador de paquetes** | Fuerza bruta 0/1 sobre subconjuntos (`facturas/package_optimizer.py`) | Con pocas facturas candidatas (decenas, no miles) enumerar todos los subconjuntos y quedarse con el mejor es simple, correcto, y no requiere una librería de optimización adicional. | Frente a un solver MILP (PuLP/OR-Tools/cvxpy): cero dependencias nuevas, cero configuración de solver, y es trivial de leer/debuggear. | **No tal cual.** Es O(2ⁿ) — con ~20 facturas ya son >1,000,000 combinaciones; se volvería lento con un portafolio real de cientos de facturas. En producción esto se reemplaza por un solver de programación entera (OR-Tools CP-SAT o PuLP/CBC) con las mismas restricciones (monto objetivo, plazo) más las que hoy faltan: concentración por deudor/sector y capital disponible por financiadora. |
| **Asistente de IA** | Gemini (`google-genai` SDK), modelo Flash, con *function calling* automático | Necesitábamos que el asistente **nunca inventara** montos o tasas — el patrón de function calling deja que el modelo solo razone y redacte, mientras cada número sale de una llamada real a `evaluate_invoice`/`recommend_package`/`publish_invoices` contra la base de datos. El SDK de Google maneja el loop de tool-calling automáticamente a partir de funciones de Python normales (con type hints + docstring), sin tener que escribir el loop de "modelo pide función → yo la ejecuto → le regreso el resultado" a mano. | Frente a construir el loop de function calling manualmente (API REST cruda): mucho menos código, y el schema de cada herramienta se genera solo desde la firma de la función. Frente a un framework como LangChain/LangGraph: para 4 herramientas y un solo agente, una dependencia completa de orquestación es peso muerto — el SDK oficial ya resuelve exactamente esto sin abstracciones extra que aprender. | **Sí, como asistente — no como el único canal para publicar.** El patrón (LLM + tools sobre servicios reales, nunca inventa números) es válido en producción. Lo que le falta antes de producción real: manejo de rate limits/reintentos con backoff, un límite explícito de gasto por conversación, logging de qué herramientas se llamaron (auditoría), y probablemente un modelo con guardrails adicionales dado que puede ejecutar una acción real (publicar) — hoy confía en el prompt del sistema para pedir confirmación, sin una capa de aprobación separada del texto del usuario. |
| **Despliegue backend** | Gunicorn + systemd + Nginx en una VPS de Vultr, sin Docker | El equipo priorizó tener el backend corriendo y depurable rápido durante el hackathon; systemd da reinicio automático y logs vía `journalctl` sin aprender Docker/Kubernetes bajo presión de tiempo. | Frente a contenedores: menos capas que depurar cuando algo falla a las 2am de un hackathon (lo vivimos varias veces: migraciones sin aplicar, conflictos de git sin resolver) — con `journalctl -u gunicorn` se ve el traceback real de inmediato. | **Funciona, pero no es cómo se vería en producción real.** Sin contenedores, escalar horizontalmente (más de una instancia) o reproducir el entorno exacto en otra máquina es manual. Un despliegue real usaría Docker + un orquestador (ECS/Cloud Run/Kubernetes) o una PaaS (Railway/Render/Fly.io) para réplicas, rollbacks atómicos, y health checks automáticos — nada de esto es difícil de agregar después, el código no depende de estar en una VPS pelada. |
| **Base de datos → migraciones** | Migraciones de Django estándar, aplicadas a mano contra la DB compartida | Es el mecanismo nativo del ORM elegido; cualquier alternativa (Alembic, SQL a mano) hubiera sido trabajo extra sin beneficio real dado que ya usamos Django. | Ninguna herramienta externa que aprender; el historial de migraciones documenta la evolución del esquema. | **El mecanismo sí, el proceso no.** Varias veces durante el desarrollo el sitio se cayó porque una migración nueva no se había corrido contra la base compartida. En producción esto se resuelve con un paso de `migrate` automático en el pipeline de despliegue (no manual), para que sea imposible desplegar código nuevo sin su migración correspondiente. |
