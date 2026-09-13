# Rediseño del constructor de paquetes de factoraje

## Objetivo

Convertir `/invoices/package` en un workspace de liquidez claro, elegante y
coherente con el resto de Factora. La liquidez objetivo será el modo principal;
la selección manual permanecerá disponible como edición explícita del paquete.

## Principios de experiencia

- El usuario empieza por cuánto efectivo necesita y el plazo del factoraje.
- La interfaz explica los importes en lenguaje humano y evita repetir “netos”.
- El efectivo estimado y la pérdida esperada dominan la jerarquía visual.
- La propuesta del algoritmo es editable antes de publicar.
- El arrastre puede mejorar la experiencia en escritorio, pero nunca será la
  única forma de agregar o retirar una factura.
- Todo importe calculado se presenta como estimación, no como oferta garantizada.

## Estructura de la pantalla

### Encabezado

El encabezado conserva la escala y el ritmo de la pantalla de Facturas. Incluye
un breadcrumb `Facturas / Nuevo paquete`, el título `Crea tu paquete de
factoraje` y una descripción breve orientada al resultado.

### Configurador de liquidez

Un panel navy compacto será el punto de entrada principal. Contendrá:

- Campo `¿Cuánto efectivo necesitas?`, con prefijo monetario y ayuda contextual.
- Selector segmentado obligatorio de 30, 60 o 90 días.
- Acción primaria `Calcular mejor combinación` con acento lime.

El modo manual no será una tarjeta paralela. La edición manual se realiza sobre
la recomendación y desde la lista de facturas disponibles.

### Resultado financiero

Después de calcular, un resumen mostrará en orden de importancia:

1. `Efectivo estimado a recibir` como dato principal.
2. Progreso respecto a la meta solicitada.
3. `Pérdida esperada` como indicador de riesgo.
4. Valor nominal del paquete y número de facturas.

El resumen incluirá esta aclaración: `Esta es una estimación después del costo
de factoraje y la pérdida esperada. El monto final dependerá de las ofertas
recibidas.`

No se usará la palabra “netos” en cada factura. En tablas y resúmenes se usará
`Estimado a recibir`.

### Composición del paquete

La sección principal se llamará `Tu paquete recomendado`. Cada factura mostrará
folio, cliente, valor de factura, estimado a recibir, pérdida esperada y una
acción explícita para retirarla.

`Facturas disponibles` será una sección secundaria. Cada factura tendrá una
acción `Agregar al paquete`. En escritorio se podrá añadir o retirar mediante
arrastre cuando sea razonable, manteniendo siempre los botones como alternativa
accesible. En móvil se usarán sólo acciones táctiles explícitas.

### Confirmación

Un panel de resumen sticky en escritorio mantendrá visibles el efectivo
estimado, la pérdida esperada, el plazo y la acción `Publicar paquete`. La acción
se deshabilita cuando el paquete está vacío o durante una publicación.

## Lenguaje visual

La pantalla reutiliza el sistema existente: navy `#0b1f44`, acento lime,
fondos blancos o neutros muy claros, tipografía sans, radios moderados, bordes
slate y sombras sutiles. Los iconos provienen del set existente. No se añaden
gradientes decorativos, glassmorphism, tipografías nuevas ni colores ajenos al
producto.

La personalidad “startup tech” proviene de una jerarquía decisiva, cifras
financieras grandes, ritmo compacto, controles precisos y microestados pulidos,
no de decoración ornamental.

## Estados y comportamiento

- Inicial: configurador visible y facturas elegibles disponibles.
- Calculando: botón y resumen muestran progreso sin bloquear toda la pantalla.
- Meta alcanzada: cobertura positiva y paquete recomendado editable.
- Meta no alcanzada: se presenta la mejor combinación disponible y el faltante.
- Paquete vacío: resumen en cero, guía para agregar facturas y publicación
  deshabilitada.
- Error de red o publicación: mensaje contextual sin perder configuración ni
  selección.
- Cambio de plazo: actualiza estimaciones y deja claro que la recomendación debe
  recalcularse.

## Accesibilidad y responsive

- Controles con labels visibles, foco perceptible y estados `disabled` claros.
- Botones de agregar/retirar con nombre accesible; el drag and drop es opcional.
- Contraste suficiente para texto y estados semánticos.
- En escritorio se usa una composición principal más resumen lateral.
- En pantallas pequeñas el resumen pasa al flujo normal y las filas se convierten
  en tarjetas compactas sin scroll horizontal obligatorio.

## Validación

- La captura de meta y plazo sigue enviando los mismos datos al API existente.
- Una recomendación selecciona facturas y actualiza efectivo estimado y pérdida.
- Agregar o retirar facturas actualiza todos los totales inmediatamente.
- La publicación utiliza exactamente la selección visible y el plazo elegido.
- Los estados vacío, error y meta insuficiente son legibles.
- ESLint y el build de producción pasan.
- Se realiza una inspección visual acotada en escritorio y móvil contra Dashboard
  y Facturas como referencias del producto.
