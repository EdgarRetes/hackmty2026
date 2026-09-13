# MVP de riesgo para factoraje

## Objetivo

Implementar una evaluación reproducible y explicable de la factura y de la empresa obligada al pago, capaz de decidir `APPROVE`, `REVIEW` o `REJECT`, recomendar anticipo y precio sensibles al plazo, y mostrar al inversionista las razones y el rendimiento esperado. El sistema usará datos mock deterministas con la misma forma que fuentes oficiales, porque el hackathon no dispone de acceso SAT autenticado.

## Alcance

Incluye modelos y migraciones, motor de elegibilidad y riesgo, pricing, persistencia de la evaluación, contrato API, seed determinista, pruebas backend, presentación frontend y documentación. No incluye onboarding KYC/KYB, descarga masiva del SAT, bureau real, cobranza, aceptación de ofertas por lote ni producción regulada.

## Enfoque seleccionado

Se usará una scorecard determinista respaldada por componentes estándar de riesgo (`PD`, `LGD`, `EAD`, madurez y dilución) en lugar de entrenar un modelo con datos sintéticos. El modelo cuantílico existente de días de atraso se retirará del camino crítico; podrá conservarse únicamente como exploración. Este enfoque es más explicable, permite casos de prueba exactos y no presenta como calibración estadística lo que sólo es un mock.

Las fuentes de referencia serán:

- SAT: estructura y estado de CFDI, RFC emisor/receptor, folio fiscal, total y cancelación.
- Banco de México: TIIE de Fondeo como tasa base, guardada como snapshot reproducible.
- INEGI/DENUE: sector SCIAN, tamaño y antigüedad aproximada del establecimiento.
- Basel CRE30/34/36: PD, LGD, EAD, madurez, concentración y dilución de cuentas por cobrar.
- IFRS 9: pérdida esperada ponderada por probabilidades, valor temporal e información prospectiva.

## Modelo de dominio

### Empresa solicitante

`Company` conservará RFC, razón social y verificación, y añadirá sector SCIAN, años operando, ventas anuales, tasa histórica de disputas y tasa histórica de dilución. Son datos mock y se marcarán con procedencia.

### Empresa deudora

`DebtorClient` añadirá RFC, sector SCIAN, tamaño, años operando, score de bureau mock, razón circulante, deuda/EBITDA, margen operativo y bandera de eventos legales. Estos campos representan un snapshot, no un proceso KYB.

### Historial de pagos

`PaymentHistory` registrará fecha de emisión, fecha de vencimiento, fecha de pago, monto facturado, monto pagado y default. `days_past_due` se derivará de vencimiento a pago; se eliminará la ambigüedad de interpretar 30 días de plazo como 30 días de atraso.

### Factura

`Invoice` añadirá UUID fiscal, RFC emisor y receptor, moneda, saldo insoluto, método de pago, estado SAT, fecha de última verificación, hash de XML, estado de disputa, evidencia de entrega y bandera de cesión previa. Se agregarán restricciones de monto/saldo positivos y fechas coherentes.

### Evaluación

`RiskAssessment` será un snapshot inmutable por ejecución con decisión, rating, score, PD, LGD, EAD, pérdida esperada de default, pérdida esperada de dilución, pérdida total, confianza, plazo, tasa de referencia, tasa anual recomendada, equivalente mensual, anticipo, costo, desembolso neto, rendimiento esperado, razones, alertas, inputs y versión de política.

## Flujo

1. `InvoiceEligibilityService` aplica reglas duras antes de puntuar.
2. `RiskScorecard` calcula métricas de pago, deudor, factura y concentración.
3. El score se mapea a rating y PD mediante una tabla explícita de política demo.
4. Se calcula `EL = PD × LGD × EAD + dilution_rate × EAD`.
5. `RiskPricingService` forma la tasa anual desde TIIE mock validada, costo operativo, margen y prima de pérdida anualizada.
6. Se persiste el snapshot y se expone por API.
7. Sólo una decisión `APPROVE` genera ofertas automáticas; `REVIEW` no genera ofertas y `REJECT` devuelve los motivos.

## Elegibilidad

Una factura se rechaza antes del scoring si no está vigente ante SAT, no es PPD, el emisor/receptor no coincide, el saldo es cero, está vencida, está disputada, ya fue cedida, carece de evidencia de entrega o repite UUID/hash. Datos insuficientes del deudor llevan a `REVIEW`, no a una aprobación neutral.

## Scorecard demo

El score de riesgo va de 0 (mejor) a 100 (peor):

- 40% comportamiento de pago: promedio y p90 de DPD, porcentaje puntual y defaults.
- 25% fortaleza del deudor: bureau mock, liquidez, apalancamiento, margen y eventos legales.
- 20% factura: madurez, monto relativo a ventas, evidencia y dilución.
- 15% concentración y sector.

La política `hackathon-v1` define bandas A-E y PD explícitas. Rating E o PD por encima del límite produce `REJECT`; datos insuficientes producen `REVIEW`. Los coeficientes son supuestos demostrativos, no una calificación regulatoria, y se documentarán como tales.

## Pricing

Para una factura aprobada:

```text
EAD = face_value × advance_percentage
EL_default = PD × LGD × EAD
EL_dilution = dilution_rate × EAD
annual_rate = reference_rate + operating_spread + capital_margin + annualized_EL_spread
period_cost = EAD × ((1 + annual_rate)^(term_days / 360) - 1)
monthly_equivalent = (1 + annual_rate)^(1 / 12) - 1
net_disbursement = EAD - period_cost
expected_investor_profit = period_cost - expected_loss - funding_cost
```

Todas las tasas se almacenan como decimales internamente y se serializan claramente como porcentajes. El plazo se calcula desde la fecha de evaluación hasta el vencimiento.

## API y frontend

- `POST /api/invoices/{id}/risk-assessment/`: crea un snapshot nuevo.
- `GET /api/invoices/{id}/risk-assessment/`: obtiene el último snapshot.
- `POST /api/invoices/{id}/offers/`: evalúa primero; para `REVIEW/REJECT` devuelve `422` con la evaluación.
- La respuesta de ofertas incluirá la evaluación vigente.
- La pantalla de ofertas mostrará decisión, rating, PD, pérdida esperada, equivalente mensual, plazo, confianza, razones y alertas.

## Datos demo

El seed será determinista y contendrá al menos:

1. Factura aprobada: CFDI vigente, historial puntual y rating B.
2. Rechazo de riesgo: deudor moroso, alta PD/concentración y rating E.
3. Rechazo de elegibilidad: CFDI cancelado o factura ya cedida.
4. Revisión manual: empresa deudora nueva sin historial suficiente.

Los registros guardarán `data_source`, `source_reference` y `as_of_date`. Los valores serán snapshots sintéticos inspirados en campos oficiales, no afirmaciones sobre empresas reales.

## Errores y trazabilidad

Los rechazos serán respuestas de negocio estructuradas, no excepciones 500. Cada evaluación conservará inputs, razones, alertas y versión de política. El caché del modelo anterior no intervendrá en el nuevo flujo. Las ofertas persistidas guardarán referencia a la evaluación usada para generarlas.

## Pruebas y aceptación

- Cada escenario demo es reproducible después de cualquier re-seed.
- Una factura rechazada o en revisión genera cero ofertas.
- La misma factura a 90 días cuesta más que a 30 días.
- Mayor PD, LGD, dilución o incertidumbre nunca aumenta el anticipo.
- La semántica de DPD usa vencimiento, no fecha de emisión.
- Un CFDI cancelado, disputado, duplicado o cedido se rechaza.
- La API entrega rating, decisión, métricas, razones y versión.
- El frontend pasa lint y build contra el backend sembrado.

## Evolución posterior

Los proveedores mock implementarán interfaces reemplazables por SAT, bureau, DENUE y datos bancarios reales. La scorecard podrá recalibrarse o sustituirse por un modelo supervisado cuando existan etiquetas suficientes, validación temporal, métricas de calibración, monitoreo de drift y gobierno de modelos. La selección automática de facturas para una meta de liquidez queda como siguiente incremento, mediante MILP/CP-SAT con restricciones de elegibilidad, concentración, capital y pérdida esperada.
