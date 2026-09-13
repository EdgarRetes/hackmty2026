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

## Cómo probar el MVP de riesgo

### Datos demo

Desde `backend/`, ejecuta:

```bash
python manage.py migrate
python manage.py seed_demo_data
```

El comando es idempotente y genera 45–65 facturas, deudores mock, historial
de pagos, publicaciones de marketplace y operaciones financiadas. También
incluye cuatro escenarios reproducibles:

- `approved`: Comercializadora del Norte, rating A.
- `risk_rejected`: Farmacias San Rafael, mora y defaults severos, rating E.
- `eligibility_rejected`: Manufacturas Regiomontanas, CFDI cancelado.
- `manual_review`: Logística Nueva Era, historial e indicadores insuficientes,
  rating N.

### Prueba por API

Levanta el backend con `python manage.py runserver` y lista las facturas:

```bash
curl http://127.0.0.1:8000/api/invoices/
```

Usa el `id` de una factura para ejecutar o consultar una evaluación:

```bash
curl -X POST http://127.0.0.1:8000/api/invoices/ID/risk-assessment/
curl http://127.0.0.1:8000/api/invoices/ID/risk-assessment/
```

Una factura aprobada genera tres ofertas:

```bash
curl -X POST http://127.0.0.1:8000/api/invoices/ID/offers/
```

Una factura `REJECT` o `REVIEW` devuelve `422` y no genera ofertas automáticas.
También puedes verificar las vistas de financiadora:

```text
GET  /api/marketplace/
GET  /api/financier/portfolio/
GET  /api/invoice-batches/{id}/offers/
POST /api/invoice-batches/{id}/accept/
```

### Prueba por interfaz

Con el backend activo, configura `NEXT_PUBLIC_API_URL` y ejecuta el frontend:

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Prueba estas rutas en `http://localhost:3000`:

```text
/invoices                 listado de facturas y publicaciones
/offers/{id}              evaluación, recomendación y ofertas
/marketplace              oportunidades para financiadoras
/financier                resumen del portafolio
/portfolio                operaciones y rendimiento
```

### Pruebas automatizadas

```bash
cd backend
python manage.py test -v 1
python manage.py makemigrations --check --dry-run

cd ../frontend
npm run lint
npm run build
```

El build requiere que `NEXT_PUBLIC_API_URL` apunte a un backend disponible.

## Algoritmo de validación de riesgo

El algoritmo tiene dos compuertas. Primero valida la factura como activo:

- CFDI `vigente` y método `PPD`.
- RFC emisor/receptor consistentes con empresa y deudor.
- Saldo positivo y vencimiento futuro.
- Evidencia de entrega, sin disputa ni cesión previa.
- UUID y hash XML no duplicados.

Después calcula un score de 0 a 100; un valor menor representa menor riesgo:

| Componente | Peso |
|---|---:|
| Historial de pagos | 40% |
| Fortaleza financiera del deudor | 25% |
| Características de la factura | 20% |
| Concentración de exposición | 15% |

El historial usa `days_past_due = max(fecha_pago - fecha_vencimiento, 0)`,
promedio, p90 y defaults. La fortaleza considera score de buró mock, liquidez,
deuda/EBITDA, margen operativo, antigüedad y eventos legales.

Las bandas son A (0–20), B (21–35), C (36–50), D (51–65), E (66–100) y N para
información insuficiente. E rechaza por riesgo; N solicita revisión manual.
Solo A–D aprobados pueden recibir ofertas.

Para una factura aprobada se calcula:

```text
EAD = saldo pendiente × porcentaje de anticipo
pérdida por default = PD × LGD × EAD
pérdida por dilución = tasa de dilución × EAD
pérdida esperada = pérdida por default + pérdida por dilución
```

La tasa anual combina TIIE de Fondeo, margen operativo, margen de capital y un
spread por pérdida esperada. Se convierte al plazo real de la factura para
obtener costo, desembolso neto y utilidad esperada del inversionista. El MVP
persiste cada evaluación junto con sus entradas, versión de política, fecha y
fuente de la tasa.

## Alcance y limitaciones

Implementado: scorecard explicable, snapshots auditables, gating de ofertas,
tasas sensibles al plazo, casos demo deterministas, marketplace, portafolio y
UI de recomendación para inversionistas.

Fuera del alcance actual: conexión real al SAT/CIEC, buró o bancos; KYC/KYB y
autorización productiva; calibración estadística regulatoria; liquidación
bancaria; monitoreo de drift; y selección óptima de facturas para un objetivo
de liquidez mediante MILP/CP-SAT.

El admin de producción está en
[api.factora.tech/admin](https://api.factora.tech/admin/). El dominio
`www.factora.tech/admin` pertenece al frontend. Los datos demo siguen campos y
definiciones de SAT, INEGI, Banxico, Basel e IFRS 9, pero sus valores son
ficticios y no constituyen una validación oficial ni una recomendación real de
inversión.
