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
