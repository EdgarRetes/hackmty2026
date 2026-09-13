# Factoraje en paquete con liquidez objetivo

## Objetivo

Permitir que una empresa publique un paquete de facturas para factoraje en
un plazo de 30, 60 o 90 días. La empresa podrá construir el paquete de forma
manual o pedir una propuesta que alcance una meta de efectivo neto y minimice
la pérdida esperada.

## Alcance

- Añadir un acceso "Crear paquete" en la esquina superior derecha de Facturas.
- Crear una pantalla o flujo de construcción de paquete con selección de plazo
  obligatoria (30, 60 o 90 días).
- Mostrar facturas pendientes, sin paquete y aprobadas automáticamente para el
  plazo elegido.
- Permitir selección manual, propuesta automática por liquidez y edición libre
  de la selección antes de publicar.
- Persistir el plazo elegido con la publicación.
- Recalcular las métricas de precio y riesgo para el plazo de paquete elegido.
- Añadir contrato API, pruebas backend y validación frontend.

No incluye aceptación de ofertas de paquetes, autenticación ni cambios al
motor de matching de financiadoras.

## Modelo y precio

`InvoiceBatch` tendrá `factoring_term_days`, con valores permitidos 30, 60 y
90. El plazo es una condición comercial del paquete; no modifica la fecha de
vencimiento original de cada CFDI.

El motor de riesgo aceptará un plazo opcional para este flujo. Cuando se
proporcione, calculará madurez, tasa, costo financiero, pérdida esperada y
desembolso contra dicho plazo; en los flujos actuales seguirá usando los días
restantes hasta el vencimiento. El snapshot de evaluación conservará el plazo
que produjo los importes.

Para cada factura elegible, el efectivo que aporta al objetivo será:

```text
efectivo_neto = anticipo - costo_financiero - pérdida_esperada
```

La API conservará los importes monetarios como strings decimales.

## Elegibilidad

Una candidata debe pertenecer a la misma empresa, estar `pending`, no tener
`batch`, y obtener decisión `APPROVE` cuando se evalúa con el plazo elegido.
Las facturas `REVIEW` y `REJECT` no se muestran como disponibles para la
selección o recomendación. El backend valida estas condiciones de nuevo al
publicar para evitar carreras o publicaciones inconsistentes.

## API

`POST /api/invoice-batches/preview/` recibirá una de estas solicitudes:

```json
{ "term_days": 60, "mode": "manual" }
```

o:

```json
{ "term_days": 60, "mode": "liquidity_target", "liquidity_target": "250000.00" }
```

La respuesta devolverá las facturas elegibles con evaluación resumida y, en
modo `liquidity_target`, una lista recomendada de ids. Incluirá el total
nominal, efectivo neto, pérdida esperada, faltante o excedente y el indicador
de que la meta fue alcanzada. Si ninguna combinación alcanza la meta, devuelve
la mejor combinación disponible y `target_reached: false`.

`POST /api/invoice-batches/` seguirá publicando el paquete, ahora con:

```json
{ "invoice_ids": [87, 97], "term_days": 60 }
```

Requiere una o más facturas, todas elegibles para el plazo y de una sola
empresa. Su respuesta incluirá `factoring_term_days` y los totales de paquete.

## Algoritmo de recomendación

Se implementará una mochila 0/1 de estados dispersos. Cada estado representa
una selección única y conserva efectivo neto acumulado, pérdida esperada,
importe nominal e ids. Tras procesar cada factura, se podan los estados
dominados: un estado es dominado si otro entrega al menos el mismo efectivo
neto con pérdida esperada no mayor.

Entre los conjuntos que alcanzan la meta se elige, en orden:

1. Menor pérdida esperada total.
2. Menor excedente sobre el efectivo neto solicitado.
3. Menor número de facturas.

Si no existe un conjunto suficiente, se devuelve el de mayor efectivo neto;
en empate se aplica la misma prioridad de menor pérdida y menor número de
facturas. Los cálculos internos usan `Decimal`, redondeados a centavos para
comparar efectivo y pérdida.

## Interfaz

El botón "Crear paquete" abrirá el constructor. El usuario elegirá el plazo,
después podrá seleccionar "Elegir facturas" o "Necesito liquidez". El modo de
liquidez muestra el campo de objetivo y solicita una propuesta.

La selección propuesta y la manual usan la misma lista editable. Cada cambio
actualiza un resumen de importe nominal, efectivo neto estimado, pérdida
esperada y progreso hacia la meta. El botón "Publicar paquete" sólo se habilita
con al menos una factura seleccionada; al publicar redirige al detalle de la
publicación existente.

## Errores y validación

- `400`: plazo no permitido, objetivo inválido, lista vacía o facturas que no
  cumplen las reglas al publicar.
- La vista de propuesta muestra un estado claro cuando la meta no puede
  alcanzarse con las facturas elegibles.
- Fallos de red y de publicación se muestran sin descartar la selección del
  usuario.

## Pruebas de aceptación

- El cálculo a 90 días produce un costo mayor y efectivo neto menor que el de
  30 días para la misma factura aprobada.
- La propuesta alcanza la meta usando efectivo neto, no importe nominal.
- Entre propuestas que alcanzan la meta, gana la de menor pérdida esperada; se
  aplican los desempates especificados.
- Una factura no aprobada, ya publicada o de otra empresa no entra al paquete.
- La publicación persiste y devuelve el plazo seleccionado.
- El frontend permite seleccionar, retirar y publicar facturas de una propuesta
  sin perder el resumen actualizado.
