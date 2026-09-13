# Factora — Factoraje Inteligente + Marketplace

**HackMTY 2026 · Reto Capital One — Autonomous Financial Intelligence & Resilience**
Área: *SMB Cash-Flow & Working Capital Intelligence (B2B)*

Demo en vivo: **[www.factora.tech](https://www.factora.tech)** · API: `api.factora.tech`

---

## El problema

Una PyME mexicana factura a 30, 60 o 90 días, pero necesita el dinero hoy. El
factoraje existe para eso, pero el mercado está roto en tres puntos: la PyME
no tiene forma de comparar ofertas (habla con una financiadora a la vez), la
decisión de crédito tarda días porque el análisis es manual, y la financiadora
evalúa mal el riesgo porque mira a la PyME en vez de mirar a **quién le debe**
a la PyME.

## La solución

Un marketplace donde varias financiadoras compiten por la misma factura:

1. La PyME sube o sincroniza sus facturas (CFDI).
2. El motor de riesgo califica al **deudor** de cada factura — el que
   realmente va a pagar — no a la PyME.
3. Tres financiadoras con personalidades distintas (conservadora, agresiva,
   especializada por sector) cotizan cada una su propio anticipo y comisión.
4. El motor de matching calcula el efectivo neto real que recibiría la PyME
   con cada oferta y las ordena.
5. La PyME acepta la mejor; el dinero se mueve (simulado vía la **Nessie API**
   de Capital One); cuando el deudor paga, se liquida a la financiadora.

Encima de eso hay dos piezas que van más allá del flujo básico:

- **Constructor de paquetes por meta de liquidez**: la PyME dice "necesito
  $200,000 a 60 días" y el sistema elige qué combinación exacta de facturas
  cubrir esa meta con la **menor pérdida esperada**.
- **Asistente de IA (Gemini)** que puede consultar el motor de riesgo,
  explicar por qué una factura no calificó, armar el paquete óptimo, y —
  si el usuario lo confirma en el chat — **publicarlo de verdad**.

---

## Arquitectura

```
┌───────────────────────────┐         ┌──────────────────────────────────────┐
│  Frontend (Vercel)         │         │  Backend (Vultr VPS)                  │
│  Next.js · React           │  HTTPS  │  Django + DRF · API-only (JSON)       │
│  TypeScript · Tailwind     │ ──────► │  Gunicorn + systemd + Nginx           │
│  Server Components         │  CORS   │                                       │
│  www.factora.tech          │         │  api.factora.tech                     │
└───────────────────────────┘         └───────────────┬──────────────────────┘
                                                       │
                         ┌─────────────────────────────┼──────────────────────┐
                         ▼                             ▼                      ▼
              ┌────────────────────┐      ┌────────────────────┐   ┌──────────────────┐
              │ PostgreSQL +        │      │ Gemini API          │   │ Nessie API        │
              │ TimescaleDB         │      │ (google-genai,      │   │ (Capital One      │
              │ (Tiger Cloud)       │      │  function calling)  │   │  sandbox)         │
              │ datos + series de   │      │ asistente que opera │   │ cuentas y         │
              │ tiempo de pagos     │      │ sobre los servicios │   │ depósitos         │
              └────────────────────┘      └────────────────────┘   └──────────────────┘
```

Monorepo: `/backend` (Django API-only) y `/frontend` (Next.js). Cada carpeta
tiene su README con el detalle técnico de esa capa
([backend](backend/README.md) · [frontend](frontend/README.md)).

### Los tres motores del backend

Todo el negocio pasa por un solo punto de verdad y tres consumidores:

```
                    core.risk_engine  (underwriting explicable)
                    elegibilidad + score 0-100 → RiskAssessment
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
mercado.matching_engine   facturas.package_optimizer   facturas.assistant
3 financiadoras cotizan    ¿qué facturas juntar para   agente Gemini que
y se rankean por           llegar a $X con la menor    consulta y ejecuta
efectivo neto              pérdida esperada?           sobre los otros dos
```

Ningún consumidor recalcula riesgo por su cuenta: todos leen el mismo
`RiskAssessment` persistido e inmutable, con su snapshot de entradas, versión
de política y tasa de referencia fechada. Eso hace que la cotización que ve la
PyME, la que ve la financiadora y la que dice el chatbot **nunca puedan
contradecirse**.

---

## Cómo correrlo

**Backend**
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # configura DATABASE_URL, DB_PASSWORD, GEMINI_API_KEY
python manage.py migrate
python manage.py seed_demo_data   # agrega --with-nessie para provisionar cuentas reales en Nessie
python manage.py runserver
```

**Frontend**
```bash
cd frontend
npm install
cp .env.local.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

`seed_demo_data` genera cuatro escenarios determinísticos para demostrar cada
salida del motor de riesgo:

| Escenario | Decisión esperada | Qué demuestra |
|---|---|---|
| `approved` | `APPROVE` / A | CFDI válido y pagador fuerte |
| `risk_rejected` | `REJECT` / E | Mora severa, defaults, pagador débil |
| `eligibility_rejected` | `REJECT` | CFDI cancelado ante el SAT |
| `manual_review` | `REVIEW` / N | Historial de pagos insuficiente |

---

## Stack: qué utilizamos, por qué, ventajas y viabilidad en producción

Resumen ejecutivo, y luego el detalle de cada decisión:

| Capa | Qué usamos | ¿Producción? |
|---|---|---|
| Lenguaje backend | Python | ✅ Sí |
| Framework backend | Django + DRF | ✅ Sí |
| Frontend | Next.js (App Router) + React + TypeScript | ✅ Sí |
| Estilos | Tailwind CSS | ✅ Sí |
| Base de datos | PostgreSQL + TimescaleDB (Tiger Cloud) | ✅ Sí |
| Motor de riesgo | Scorecard determinístico explicable | ⚠️ Arquitectura sí, calibración no |
| Motor de pricing | Variantes determinísticas sobre la recomendación central | ⚠️ Sirve, pero limita la competencia real |
| Optimizador de paquetes | Fuerza bruta 0/1 (knapsack) | ❌ No escala — requiere solver |
| Asistente IA | Gemini (Flash) + function calling | ✅ Sí, con guardrails adicionales |
| Movimiento de dinero | Nessie API (sandbox Capital One) | ❌ Sandbox — requiere SPEI/banco real |
| Autenticación | Cookie de rol, sin usuarios reales | ❌ No — es lo primero a construir |
| Deploy backend | Gunicorn + systemd + Nginx en Vultr | ⚠️ Funciona, no escala horizontalmente |
| Deploy frontend | Vercel | ✅ Sí |

---

### 1. Python como lenguaje único del backend

**Qué usamos:** Python en toda la capa de servidor.

**Por qué:** El corazón del producto es un motor de riesgo financiero. Python
es el lenguaje dominante en ingeniería de riesgo en banca real, y el
ecosistema de integración fiscal mexicana (`satcfdi`, `cfdiclient` para
descarga masiva de CFDI vía e.firma) es nativo de Python. Un solo lenguaje en
todo el backend reduce puntos de falla en 36 horas.

**Ventaja sobre otras opciones:** Frente a Node/TypeScript en el backend:
tendríamos que salir a buscar librerías fiscales mexicanas que no existen con
la misma madurez, o mezclar dos runtimes. Frente a Java/Go: velocidad de
iteración mucho menor para un hackathon, sin ganancia real de rendimiento en
un sistema cuyo cuello de botella es la base de datos, no el CPU.

**¿Producción?** **Sí.** Es la elección estándar en fintech para lógica de
riesgo. El único punto a vigilar en escala es que Python es más lento por
request que Go/Java — pero eso se resuelve con más réplicas, no cambiando de
lenguaje, y aquí ninguna operación es CPU-bound salvo el optimizador (ver #8).

---

### 2. Django + Django REST Framework (API-only)

**Qué usamos:** Django + Django REST Framework, exclusivamente como API JSON —
sin templates, sin HTML servido desde Django.

**Por qué:** El modelo de datos es inherentemente relacional (empresa →
factura → deudor → evaluación de riesgo → oferta → financiadora). Django trae
ORM, migraciones, constraints a nivel de base de datos y panel de
administración desde el minuto cero, y DRF agrega serializers y manejo
consistente de errores. Además trae protecciones de seguridad activadas por
default (CSRF, escape de SQL, XSS), lo cual importa en un sistema que
eventualmente manejaría credenciales fiscales (CIEC/e.firma) y mueve dinero.

**Ventaja sobre otras opciones:** Frente a Flask/FastAPI: no hubo que armar
ORM, migraciones ni admin a mano — eso costó **cero** tiempo de hackathon.
Frente a Express/Nest: el ORM de Django modela relaciones complejas y
constraints de integridad (`CheckConstraint` de monto positivo, fecha de
vencimiento ≥ emisión) sin dependencias externas.

**¿Producción?** **Sí** — Django corre Instagram y Disqus. Lo que faltaría
agregar: autenticación real (DRF SimpleJWT/OAuth2), rate limiting por
endpoint, logging estructurado, y paginación en los listados (hoy
`/api/invoices/` devuelve todo sin paginar, lo cual es correcto con 80
facturas y no lo sería con 80,000).

---

### 3. Next.js (App Router) + React + TypeScript en el frontend, separado del backend

**Qué usamos:** Next.js con App Router, React y TypeScript, desplegado en
Vercel. El frontend consume la API de Django por HTTPS con CORS.

**Por qué separarlo en vez de usar templates de Django:** Cada pieza va a la
plataforma diseñada para ella — Next.js en Vercel (CDN global, previews por
PR, rollback en un clic), Django en un VPS. Es el patrón real de arquitectura
fintech en México (Konfío, Klar, Xepelin operan así). Y como el backend ya
expone todo vía DRF, el día que haya app móvil el backend ya está listo sin
reescribir nada.

**Por qué App Router y Server Components:** casi todas las pantallas solo
muestran datos financieros. Con Server Components ese fetch ocurre **en el
servidor**, nunca en el navegador del usuario — no se expone lógica de
negocio ni se manda JavaScript innecesario al cliente. Solo tres piezas son
interactivas (`"use client"`): la tabla de selección de facturas, el
constructor de paquetes y el chat de IA.

**Ventaja sobre otras opciones:** Frente a Vite + React Router: habría que
construir a mano el SSR, el fetching por ruta y el manejo de errores por
pantalla — el App Router lo da con `page.tsx` + `error.tsx` por segmento.
Frente al Pages Router clásico: menos JS enviado al cliente.

**Costo reconocido:** dos despliegues en vez de uno, y CORS entre servicios.
Lo pagamos varias veces durante el hackathon (un error de configuración de
CORS o de URL rompe todo el frontend), pero a cambio obtuvimos despliegues
independientes: se puede desplegar el frontend sin tocar el backend.

**¿Producción?** **Sí.** Next.js + Vercel es una combinación de producción
estándar. Nada aquí hay que migrar para escalar.

---

### 4. Tailwind CSS

**Qué usamos:** Tailwind con configuración CSS-first (sin
`tailwind.config.js`; los tokens de marca viven en `globals.css`).

**Por qué:** Construimos ~14 pantallas con un lenguaje visual consistente sin
diseñar un design system desde cero ni traer una librería de componentes que
imponga su propia estética.

**Ventaja sobre otras opciones:** Frente a MUI/Chakra: la interfaz no se ve
"de librería", que en un reto donde Diseño y Experiencia vale 20% de la
calificación importa. Frente a CSS Modules: cero archivos de estilos paralelos
que mantener sincronizados con los componentes.

**¿Producción?** **Sí.** Lo único a mejorar antes de crecer el equipo: extraer
a componentes los patrones repetidos (tarjetas, botones) — hoy hay bastante
`className` duplicado entre pantallas similares.

---

### 5. Base de datos: relacional, PostgreSQL, con Tiger Cloud/TimescaleDB de extensión

#### 5.1 Por qué una base de datos relacional y no una no-relacional

**Qué usamos:** un modelo relacional con tablas y llaves foráneas
(`Company` → `Invoice` → `DebtorClient`, `InvoiceBatch`, `Offer`,
`RiskAssessment`, `PaymentHistory`), no documentos.

**Por qué:** el dominio del problema **es** un grafo de relaciones estrictas:
una factura pertenece a una sola empresa y a un solo deudor, un paquete
agrupa varias facturas, una oferta referencia una evaluación de riesgo
específica. Un producto que mueve dinero necesita que la base de datos misma
haga cumplir esas reglas — no solo el código de la aplicación — con llaves
foráneas y `CheckConstraint` (monto > 0, vencimiento ≥ emisión, saldo insoluto
positivo). Si esa integridad vive solo en Python y no en el esquema, un bug o
un script mal corrido puede dejar datos financieros inconsistentes sin que
nadie se entere hasta que ya causó un problema real.

**Ventaja sobre una base no-relacional (MongoDB, DynamoDB, etc.):** en un
modelo de documentos, esas mismas relaciones e integridad hay que
reimplementarlas a mano en la aplicación — joins simulados, validación de
consistencia entre documentos, transacciones multi-documento más complejas de
razonar. Las bases no-relacionales ganan cuando el esquema cambia
constantemente o el acceso es mayormente por llave única (catálogos de
producto, sesiones, logs) — no es el caso aquí: el esquema es estable y casi
toda consulta relevante ("las ofertas de este paquete", "el historial de
pagos de este deudor") es, por definición, un join.

#### 5.2 Por qué PostgreSQL sobre otros motores relacionales

**Qué usamos:** PostgreSQL.

**Por qué:** de los motores relacionales open-source maduros, Postgres tiene
el soporte de tipos más completo para este dominio — `JSONField` nativo
consultable (lo usamos para guardar `reasons`, `warnings` y el snapshot
completo de entradas de cada `RiskAssessment` sin normalizar cada campo en su
propia tabla), `DecimalField` con precisión exacta para dinero, y
constraints (`CheckConstraint`, `UniqueConstraint`) expresivos a nivel de
esquema. Django además trata a Postgres como su base de datos de referencia —
el soporte es el más completo del ORM.

**Ventaja sobre otras opciones:** frente a MySQL: mejor soporte de JSON
consultable y de constraints complejos (`CheckConstraint` con múltiples
columnas, como la validación de fecha de vencimiento). Frente a SQL Server u
Oracle: sin licenciamiento, y el mismo nivel de robustez transaccional para
este caso de uso. Frente a SQLite (que el proyecto sí usa, pero solo en
desarrollo local sin `DATABASE_URL`): SQLite no soporta el nivel de
concurrencia ni las extensiones que necesita un backend con tráfico real.

**¿Producción?** **Sí**, sin reservas — Postgres es el motor relacional
estándar en fintech.

#### 5.3 Tiger Cloud y TimescaleDB

**Qué usamos:** el servicio de Postgres gestionado de Tiger Cloud, con la
extensión TimescaleDB disponible. Desde la aplicación se ve y se comporta
exactamente como cualquier Postgres estándar (mismo driver `psycopg`, mismo
ORM de Django, misma cadena de conexión) — no hay código específico de
Timescale hoy en el proyecto.

**Otras opciones en el mercado:** para Postgres gestionado sin necesidad de
Timescale, existen Amazon RDS/Aurora, Google Cloud SQL, Supabase, Neon o
Railway — todas funcionarían igual de bien para la parte relacional del
proyecto tal como está hoy.

**Por qué vale la pena como elección extensible a futuro:** Tiger Data
(TimescaleDB) sirve específicamente para series de tiempo a escala, que es
exactamente la forma que toman los datos de un mercado de facturación activo.
Hoy el proyecto no la explota, pero es la extensión natural si el marketplace
crece:

> Tiger Data podría utilizarse para manejar la **información temporal
> generada por el mercado de facturas**, como bids, subastas, transacciones,
> precios, yields y volumen negociado.
>
> Esto permitiría analizar el comportamiento histórico del mercado y calcular
> métricas como **precios de mercado, descuentos, liquidez, spreads y
> tendencias**, utilizando las operaciones de las subastas para generar
> *price discovery*.
>
> Por ejemplo, las operaciones de facturas con características similares
> podrían analizarse a lo largo del tiempo para estimar un precio o rango de
> mercado, considerando variables como vencimiento, riesgo, sector y
> comportamiento histórico.
>
> Tiger Data complementaría a PostgreSQL: PostgreSQL manejaría los datos
> principales de la aplicación, mientras que TimescaleDB sería especialmente
> útil para el **market data y análisis de series temporales**.

**⚠️ Gotcha real que nos costó tiempo:** la cadena de conexión que da Tiger
Cloud **no incluye la contraseña**. Hay que pasarla aparte en `DB_PASSWORD` y
mezclarla después de parsear `DATABASE_URL` — documentado en
[backend/README.md](backend/README.md).

**¿Producción?** **Sí.** Postgres gestionado es estándar en fintech. Falta
activar y verificar backups, réplicas de lectura y point-in-time recovery
(Tiger Cloud lo ofrece; no lo configuramos para el demo).

---

### 6. Motor de riesgo: scorecard determinístico explicable

> **Este es el cambio más importante respecto al plan original.** Planeamos
> regresión cuantílica (`GradientBoostingRegressor` con `loss="quantile"`).
> La construimos, y luego la reemplazamos. Aquí está el porqué.

**Qué usamos:** un scorecard determinístico de dos compuertas
(`backend/core/risk_engine.py`):

1. **Elegibilidad del activo** — CFDI vigente, método PPD, RFC emisor/receptor
   consistentes, saldo positivo, vencimiento futuro, evidencia de entrega, sin
   disputa, sin cesión previa, sin UUID ni hash XML duplicado.
2. **Evaluación crediticia** — score 0–100 ponderado:

   | Componente | Peso |
   |---|---:|
   | Historial de pagos del deudor | 40% |
   | Fortaleza financiera del deudor | 25% |
   | Características de la factura | 20% |
   | Concentración de exposición | 15% |

   Bandas: A (0–20), B (21–35), C (36–50), D (51–65), E (66–100), N para
   información insuficiente. E rechaza; N manda a revisión manual; solo A–D
   generan ofertas.

**Por qué cambiamos de regresión cuantílica a scorecard:** La justificación
original de la regresión cuantílica era correcta *en el papel* — un modelo
global que le presta patrón a clientes con poco historial, como Amazon
Forecast. El problema apareció al implementarla: **no teníamos datos reales
con qué entrenarla**. Un modelo entrenado sobre datos sintéticos no aprende
riesgo crediticio; aprende a reproducir los arquetipos con los que nosotros
mismos generamos los datos. Predecir bien esos datos no prueba nada, y
presentarlo como "modelo de ML" ante jueces con criterio financiero sería
vender humo. El scorecard, en cambio: es reproducible, cada decisión se
explica con razones concretas en español que el usuario ve en pantalla, es
auditable línea por línea, y las pruebas tienen resultados esperados estables.

**Ventaja sobre otras opciones:**
- Frente a ML entrenado con datos sintéticos: sin riesgo de overfitting a
  ruido inventado, y explicable ante un regulador (la CNBV puede leer la
  fórmula; no puede leer los pesos de un gradient boosting).
- Frente a cadenas de Markov: no necesita volumen de historial por estado para
  estimar una matriz de transición confiable.
- Frente a análisis de supervivencia (Kaplan-Meier/Cox): no sufre intervalos
  de confianza que se ensanchan cuando hay pocas observaciones por cliente.

**Cómo se convierte en precio** (fórmulas completas en
[backend/README.md](backend/README.md#loss-and-price-formulas)):

```text
EAD = saldo insoluto × porcentaje de anticipo
pérdida esperada = (PD × LGD × EAD) + (tasa de dilución × EAD)
tasa anual = TIIE de Fondeo + spread operativo + margen de capital
             + min(spread de pérdida anualizada, 30%)
desembolso neto = EAD − costo del periodo
```

La TIIE es un snapshot fechado de Banco de México (6.49%, 2026-09-11) que se
**persiste con cada evaluación** junto con su URL, para que una evaluación
vieja nunca cambie cuando se mueven las tasas.

**¿Producción?** **La arquitectura sí; la calibración no.** El esquema de dos
compuertas con score ponderado es exactamente cómo funcionan scorecards de
crédito reales. Lo que **no** puede salir a producción tal cual: las bandas de
PD/LGD/anticipo están puestas a mano como supuestos de prototipo, no
calibradas estadísticamente ni aprobadas por CNBV. Para producción real hace
falta: outcomes etiquetados reales, validación temporal, calibración de
probabilidades, monitoreo de drift y gobernanza de modelo. **Y ahí sí vuelve a
tener sentido la regresión cuantílica** — con datos reales, es el siguiente
paso natural sobre este scorecard, no un reemplazo de su lógica de
elegibilidad.

---

### 7. Motor de pricing y matching

> **Segundo cambio respecto al plan.** Planeamos optimización convexa con
> CVXPY. La construimos y también la reemplazamos.

**Qué usamos:** tres financiadoras simuladas (`mercado/matching_engine.py`)
que ajustan anticipo y spread alrededor de la recomendación central del
underwriting, cada una con su personalidad:

| Financiadora | Perfil | Comportamiento |
|---|---|---|
| Financiera del Bajío | Conservadora | Menor anticipo, menor tasa |
| Capital Ágil MX | Agresiva | Mayor anticipo, mayor tasa |
| Fondeo Azteca | Especializada | Mejor oferta si el sector SCIAN del deudor es su especialidad (manufactura) |

El matching calcula el **efectivo neto real** que recibe la PyME con cada
oferta (después del costo del plazo completo) y las rankea por ese número.

**Por qué cambiamos de CVXPY:** la formulación convexa original tenía un bug
real y revelador — penalizaba el **monto** financiado al cuadrado en vez de la
**fracción** de anticipo, así que el término cuadrático dominaba al ingreso
lineal en montos reales de factura y el solver colapsaba a su cota inferior
sin importar el riesgo: las tres financiadoras cotizaban idéntico. Lo
arreglamos, pero la lección quedó: un solver convexo con constantes calibradas
a mano no producía ofertas más diferenciadas que variantes explícitas sobre
una recomendación central — solo era mucho más difícil de explicar y depurar.
Como el underwriting ya calcula la tasa técnicamente correcta (costo de
fondeo + pérdida esperada + márgenes), las financiadoras solo necesitan
diferenciarse **alrededor** de ella.

**Ventaja sobre otras opciones:** Frente a CVXPY: transparente y auditable
(se ve exactamente por qué la agresiva ofrece 95% y la conservadora 80%),
sin dependencia de solver, y determinístico. Frente a reglas por umbral
simples: sigue siendo sensible al riesgo, porque la base sobre la que varía
**es** la recomendación del scorecard.

**¿Producción?** **Sirve como simulación, pero es su límite conceptual.** En
producción las financiadoras son entidades reales con su propio apetito de
riesgo, costo de fondeo y capital disponible — no variantes de una fórmula
central. La evolución real es un API de bidding donde cada financiadora
conecta su propio motor, y el marketplace solo ordena y liquida. Ahí sí, la
optimización convexa vuelve a tener sentido **del lado de cada financiadora**,
para resolver simultáneamente anticipo y tasa contra su límite de riesgo.

---

### 8. Optimizador de paquetes por meta de liquidez

**Qué usamos:** enumeración exhaustiva de subconjuntos (knapsack 0/1) en
`facturas/package_optimizer.py`. Dada una meta de efectivo y un plazo
(30/60/90 días), evalúa cada factura elegible a ese plazo y elige la
combinación que cubre la meta **minimizando la pérdida esperada**, desempatando
por menor excedente y menos facturas.

**Por qué:** con decenas de facturas candidatas, enumerar es simple, es
exacto (no aproximado), y no requiere configurar un solver.

**Ventaja sobre otras opciones:** frente a un heurístico greedy: el resultado
es óptimo, no aproximado. Frente a un solver MILP: cero dependencias nuevas y
trivial de leer y depurar.

**¿Producción?** **No tal cual.** Es O(2ⁿ): con 20 facturas ya son más de un
millón de combinaciones, y un portafolio real tiene cientos. La sustitución
directa es un solver de programación entera (**OR-Tools CP-SAT** o PuLP/CBC)
con las mismas restricciones más las que hoy faltan: límites de concentración
por deudor y por sector, y capital disponible por financiadora.

---

### 9. Asistente de IA: Gemini con function calling

**Qué usamos:** Gemini (modelo Flash) vía el SDK oficial `google-genai`, con
*function calling* automático sobre cinco herramientas
(`facturas/assistant.py`):

| Herramienta | Qué hace |
|---|---|
| `listar_facturas_disponibles` | Facturas elegibles con riesgo, tasa y efectivo neto estimado |
| `detalle_factura` | Underwriting completo: decisión, rating, PD, razones, advertencias |
| `simular_paquete` | Compara las 3 financiadoras para un conjunto de facturas dado |
| `optimizar_paquete_por_liquidez` | Corre el optimizador para una meta de efectivo y plazo |
| `publicar_paquete` | **Publica de verdad** la publicación en el marketplace |

**Por qué function calling y no un prompt con datos inyectados:** porque el
requisito no negociable era que el asistente **nunca invente un número**. Con
este patrón el modelo solo razona y redacta; cada monto, tasa y decisión de
riesgo sale de una llamada real a las mismas funciones que usa el resto de la
aplicación, contra la base de datos de producción. Si el motor de riesgo
rechaza una factura, el chatbot lo dice y explica por qué — no puede
"convencerse" de lo contrario.

**Ventaja sobre otras opciones:** Frente a escribir el loop de tool-calling a
mano contra la API REST: el SDK genera el esquema de cada herramienta desde
la firma y el docstring de la función Python, y maneja el ciclo completo.
Frente a LangChain/LangGraph: para un agente con cinco herramientas, un
framework de orquestación completo es peso muerto y una abstracción más que
aprender y depurar.

**Va más allá de "explicar ofertas en lenguaje natural":** el asistente
**ejecuta**. Le puedes decir *"necesito $200,000 a 60 días"* y arma el paquete
óptimo; le dices *"publícala"* y la publicación queda creada, con el enlace
directo en el chat y la pantalla actualizándose sola.

**¿Producción?** **Sí como patrón**, con tres cosas que faltan: reintentos con
backoff ante rate limits, límite de gasto por conversación, y — lo más
importante — una capa de confirmación **fuera del texto del modelo** antes de
ejecutar una acción irreversible. Hoy `publicar_paquete` se dispara porque el
system prompt le indica pedir confirmación primero; en producción, publicar
debería requerir un clic explícito del usuario en la UI, no la interpretación
del modelo sobre si el usuario ya dijo que sí.

---

### 10. Nessie API (Capital One) para el movimiento de dinero

**Qué usamos:** el sandbox de Nessie (`core/nessie_client.py`) para provisionar
clientes y cuentas de las empresas y financiadoras, y registrar los depósitos
del historial de pagos como transacciones bancarias reales del sandbox
(`seed_demo_data --with-nessie`).

**Por qué:** el reto de Capital One recomienda explícitamente Nessie para
evitar construir infraestructura bancaria desde cero, y nos permite demostrar
el flujo completo hasta el movimiento de fondos sin simularlo con un número en
una tabla.

**Aprendizajes reales de la integración:** la autenticación va como query param
`?key=`, no como header (la documentación interactiva no lo muestra
confiablemente); `Deposit.amount` es entero, sin centavos; y el sandbox es un
entorno compartido lleno de datos duplicados de otros equipos, así que el
código reutiliza IDs guardados en vez de crear entidades nuevas en cada
re-seed.

**¿Producción?** **No — es un sandbox por diseño.** En producción esto se
sustituye por dispersión real vía SPEI (directo con un banco o mediante un
agregador de pagos mexicano como STP o Kuspit), con conciliación automática al
pago del deudor y trazabilidad contable completa.

---

### 11. Despliegue: Vultr (backend) + Vercel (frontend)

**Qué usamos:** Backend en un VPS Ubuntu de Vultr con Gunicorn + systemd +
Nginx, **sin Docker**. Frontend en Vercel con dominio `.tech`.

**Por qué sin Docker (cambio vs. el plan original):** planeamos Docker, pero
durante el hackathon priorizamos poder depurar rápido. Con systemd, un
`journalctl -u gunicorn` muestra el traceback real de inmediato — y lo
necesitamos varias veces (migraciones sin aplicar, conflictos de git sin
resolver que dejaban Python inválido en el servidor). Una capa menos entre el
error y nosotros valía más que la portabilidad a las 2 a.m.

**Ventaja sobre otras opciones:** frente a contenedores en un hackathon: menos
piezas que puedan fallar. Frente a una PaaS: control total del servidor y
cumple el requisito de usar Vultr.

**¿Producción?** **Funciona, pero no es como se vería.** Sin contenedores,
escalar a más de una instancia o reproducir el entorno exacto es manual.
Producción real usaría Docker con un orquestador (Cloud Run/ECS/Kubernetes) o
una PaaS (Railway/Render/Fly.io) para réplicas, rollbacks atómicos y health
checks. Nada del código depende de estar en un VPS pelado, así que la
migración es directa. **Y lo más urgente:** un paso de `migrate` automático en
el pipeline de despliegue — varias caídas del sitio durante el desarrollo
fueron exactamente esto: código nuevo desplegado sin su migración.

---

### 12. Autenticación y KYC/KYB

**Qué usamos:** una cookie httpOnly con el rol (`sme` / `financier`) y un flujo
de onboarding (`/register`) con la forma de un expediente real: RFC, acta
constitutiva, domicilio, datos fiscales y bancarios para PyMEs; INE,
verificación facial, comprobante de domicilio y datos bancarios para
financiadoras.

**Por qué:** el objetivo del demo era mostrar **ambas** experiencias del
marketplace sin invertir horas en un sistema de autenticación que no era lo
que se estaba evaluando.

**¿Producción?** **No, y es lo primero que hay que construir.** Hoy no hay
verificación de identidad y el onboarding no almacena ni valida ningún
documento. Producción real necesita: autenticación real (NextAuth/Auth0/Clerk +
sesiones ligadas a cuentas en el backend), y sobre todo el expediente
regulatorio que hoy solo está esbozado en la UI:

- **PyMEs:** validación de formato de RFC, cruce contra la
  [lista 69-B del SAT](https://69b.mx/listado-69b) (EFOS, +14,000 RFCs),
  Constancia de Situación Fiscal, INE y comprobante de domicilio.
- **Financiadoras:** cruce contra el
  [Padrón de Entidades Supervisadas de la CNBV](https://www.cnbv.gob.mx) y el
  [SIPRES de CONDUSEF](https://webapps.condusef.gob.mx/SIPRES).
- **AML:** la Lista de Personas Bloqueadas de la UIF es confidencial (solo
  accesible a entidades obligadas), pero la
  [lista SDN de OFAC](https://sanctionssearch.ofac.treas.gov) sí es pública y
  consultable.

---

### 13. Integración fiscal (SAT / CFDI)

**Qué usamos hoy:** el modelo `Invoice` tiene la **forma** de un CFDI real
(`cfdi_uuid`, `issuer_rfc`, `receiver_rfc`, `payment_method`, `sat_status`,
`xml_hash`) y el motor de riesgo valida esos campos como compuerta de
elegibilidad — pero los valores son ficticios, generados por el seed. **No hay
conexión en vivo con el SAT.**

**Por qué no lo conectamos:** la descarga masiva del SAT requiere e.firma
(certificado `.cer` + llave `.key` + contraseña) del contribuyente. Sin
empresas reales que nos dieran su e.firma, la integración no se podía
demostrar de punta a punta — y pedirle credenciales fiscales a un juez para
una demo no es aceptable.

**Cómo se conectaría en producción:** las librerías ya están identificadas y
activamente mantenidas — `satcfdi` (parseo/creación de CFDI, Constancia de
Situación Fiscal, consulta 69-B) y `cfdiclient` (servicio web oficial de
Descarga Masiva vía e.firma). La ruta de e.firma evita el captcha que sí tiene
la ruta CIEC. Como los campos del modelo ya coinciden con los del CFDI real,
la integración es un adaptador que llena esos campos, no un rediseño del
esquema. Buena práctica documentada: usar la credencial solo en memoria
durante la sesión, sin persistirla.

---

## Qué cambió respecto al plan original, y por qué

Documentamos esto explícitamente porque los tres cambios fueron decisiones de
ingeniería tomadas al chocar con la realidad, no recortes por falta de tiempo:

| Plan original | Lo que quedó | Razón |
|---|---|---|
| Regresión cuantílica (sklearn) | Scorecard determinístico explicable | Sin datos reales, un modelo de ML solo memoriza los arquetipos sintéticos con los que lo generamos. El scorecard es auditable y honesto sobre lo que sabe. |
| Optimización convexa con CVXPY | Variantes determinísticas sobre la recomendación central | El solver colapsaba a su cota inferior (bug de formulación que encontramos y arreglamos); una vez arreglado, no producía ofertas más diferenciadas que las variantes explícitas, y era mucho más difícil de explicar. |
| Docker en Vultr | Gunicorn + systemd + Nginx | Depuración inmediata durante el hackathon pesó más que la portabilidad. |
| Knapsack "si sobra tiempo" | Construido, y expuesto también al chatbot | Sobró tiempo y resultó ser una de las piezas más diferenciadoras. |
| Gemini para explicar ofertas | Gemini que además **ejecuta** (publica paquetes) | El function calling permitió ir de "explicar" a "operar" sin sacrificar la garantía de que no inventa números. |

`scikit-learn`, `pandas` y `cvxpy` siguen en `requirements.txt` y
`core/pricing_agents.py` conserva la implementación convexa original: quedan
como referencia de lo que se evaluó, pero **ningún endpoint los usa hoy**.

---

## Estado actual y siguientes pasos

**Funciona hoy, verificado end-to-end contra la base de datos de producción:**
underwriting explicable con cuatro escenarios determinísticos, cotización de
tres financiadoras, ranking por efectivo neto, publicaciones de 1 o más
facturas, aceptación por parte de la financiadora, constructor de paquetes por
meta de liquidez, asistente Gemini que consulta y publica, y provisión de
cuentas/depósitos en Nessie.

**Para llevarlo a producción, en orden de prioridad:**

1. Autenticación real + expediente KYC/KYB contra listas públicas (69-B, CNBV,
   CONDUSEF, OFAC).
2. Migraciones automáticas en el pipeline de despliegue.
3. Integración real con el SAT vía e.firma (`satcfdi` / `cfdiclient`).
4. Dispersión real de fondos por SPEI en lugar del sandbox de Nessie.
5. Sustituir el optimizador por OR-Tools CP-SAT con restricciones de
   concentración y capital.
6. Recalibrar el scorecard con outcomes reales — y ahí sí, regresión
   cuantílica encima, con gobernanza de modelo.
7. Contenerizar y escalar horizontalmente.

---

## Documentación por servicio

- **[backend/README.md](backend/README.md)** — arquitectura interna, fórmulas
  completas de pérdida y precio, fundamentación en fuentes oficiales (SAT,
  Banxico, INEGI, Basel CRE30/34/36, IFRS 9), semántica de pagos y contrato de
  la API.
- **[frontend/README.md](frontend/README.md)** — patrón de obtención de datos,
  manejo de errores por ruta, roles sin login real, y el panel del asistente.
- **[backend/DEPLOY.md](backend/DEPLOY.md)** — comandos exactos de despliegue
  en el VPS.
- **[AGENTS.md](AGENTS.md)** — brief del proyecto y convenciones de código.
