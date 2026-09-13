# Frontend — Factora (Next.js App Router)

The client for Factora, a factoring marketplace where Mexican SMEs
(**empresas/PyMEs**) publish invoices for financing and lenders
(**financiadoras**) bid on them. Two experiences, one codebase: which one you
see depends on a role you pick on `/login`, not a real account.

## Stack

- Next.js (App Router), React, TypeScript
- Tailwind CSS (CSS-first config — no `tailwind.config.js`, see `src/app/globals.css`)
- `react-markdown` + `remark-gfm` — renders the AI assistant's replies (tables, bold, lists)
- Deploy target: **Vercel**

No client-side state library, no CSS-in-JS, no component library. Server
Components fetch data directly from the Django API at request time; the few
interactive pieces (forms, the invoice table, the AI chat panel) are scoped
`"use client"` components.

## Getting started

```bash
npm install
cp .env.local.example .env.local   # set NEXT_PUBLIC_API_URL to your backend
npm run dev
```

Open http://localhost:3000. It calls the backend's `GET /api/health/` from the
homepage's Server Component — that round trip is the proof the two services
are wired together.

`NEXT_PUBLIC_API_URL` is embedded at build time and is genuinely public (it's
just the backend's base URL, no secret) — in production it's set in the
Vercel project's environment variables. The backend's `CORS_ALLOWED_ORIGINS`
must include whatever origin this app is served from.

## Roles, without a real login

There's no password, no user table on this side. `/login` sets an httpOnly
cookie (`factora_role`, via `POST /api/session`, see
`src/app/api/session/route.ts`) to either `sme` or `financier`, and
`AppShell` + `routeBelongsTo` (`src/lib/session.ts`) use it to pick the nav,
the home route, and gate which pages render for which role. `/register`
walks through a short KYB/KYC-shaped onboarding form (RFC, acta constitutiva,
INE, verificación facial, etc.) that ends the same way — it sets the role
cookie and redirects. **No document, credential, or file uploaded there is
stored anywhere** — this is a demo, not a real onboarding pipeline.

| Role | Home | What they can do |
|---|---|---|
| `sme` (PyME) | `/` | See a financial dashboard, list/select invoices (`/invoices`), build a package by liquidity target (`/invoices/package`), review its own publications (`/publications`, `/publications/[id]`), see financing history (`/financing`), review single-invoice offers (`/offers/[invoiceId]`), and use the AI assistant. |
| `financier` (Financiadora) | `/financier` | See a portfolio dashboard, browse open marketplace opportunities (`/marketplace`, `/marketplace/[batchId]`), and review/accept offers (`/financier/offers`, `/portfolio`). |

## Data fetching pattern

Every page under `src/app/*/page.tsx` is an `async` Server Component that
calls a plain `async` function from `src/lib/*.ts` (e.g. `getInvoices()`,
`getDashboardData()`), which in turn calls `apiRequest()` (`src/lib/api.ts`) —
a thin `fetch` wrapper against `NEXT_PUBLIC_API_URL` with `cache: "no-store"`
(always fresh, this is financial data) and a consistent error shape
(`ApiError` with `status` + parsed `detail`).

If that fetch throws, the nearest `error.tsx` in the route segment catches it
— every route has its own, each showing what actually broke (`error.message`
and `error.digest`) instead of a silent blank page. This is a real,
recurring lesson from this project: a Server Component's fetch to the
backend **never appears in the browser's Network tab** (it runs on the
server, not in the visitor's browser) — the only way to see what failed is
this `error.digest` cross-referenced against the hosting platform's server
logs (Vercel's Runtime Logs for this app).

The one deliberately client-side, live round trip is the AI assistant
(`src/components/invoices/invoice-assistant-panel.tsx`): it calls the backend
directly from the browser (`src/lib/invoice-assistant.ts`), because a chat
needs to be interactive, not rendered once per page load.

## The AI assistant

A floating "Asistente IA" button on `/invoices` opens a chat backed by
`POST /api/invoices/assistant/` (Gemini + function calling on the Django
side — see `backend/facturas/assistant.py`). It can list eligible invoices,
explain why one didn't qualify, simulate or optimize a package for a
liquidity target, and — if you confirm — actually publish it. When it does,
the response carries `published_batch_id`, and the panel shows a **"Ver
publicación →"** link and calls `router.refresh()` so the rest of the page
(counts, statuses) updates without a manual reload.

## Project structure

```
src/app/            routes (App Router) — one page.tsx + error.tsx per screen
src/components/     UI, grouped by feature (invoices/, offers/, marketplace/, dashboard/, auth/, ...)
src/lib/            data-fetching functions + API client, one file per domain
src/app/globals.css Tailwind theme tokens (@theme inline) + the assistant's markdown styles
```

## Verification habits this project relies on

- `npx tsc --noEmit` and `npm run lint` before considering any change done.
- Real screenshots (Playwright) for anything visual — a passing type-check
  proves the code compiles, not that a screen looks or works right.
- Testing against the **real** backend (local Django, or even production's
  API directly) rather than mocks, since several real bugs here only showed
  up against real data shapes (a status value with no matching UI case, a
  money field that needed cents-scaling, a Decimal a JSON encoder couldn't
  serialize).

## Decisiones técnicas: qué usamos, por qué, y si serviría en producción

| Pieza | Qué usamos | Por qué lo elegimos | Ventaja sobre otras opciones | ¿Sirve en producción? |
|---|---|---|---|---|
| **Framework** | Next.js, App Router | Necesitábamos páginas que hicieran fetch de datos financieros en el servidor (nunca exponer lógica de negocio al navegador) y navegación entre ~13 pantallas con layouts compartidos (sidebar, topbar) sin reescribirlos en cada una. El App Router da exactamente eso: Server Components por defecto, layouts anidados, y `error.tsx`/`loading.tsx` por segmento de ruta gratis. | Frente a Create React App/Vite + React Router: no hay que armar el fetching de datos, el manejo de errores por ruta, ni el SSR a mano — viene resuelto por el framework. Frente al Pages Router (Next.js clásico): los Server Components evitan mandar JS innecesario al cliente para pantallas que solo muestran datos. | **Sí.** Next.js en Vercel es una combinación de producción estándar, usada por miles de aplicaciones reales — no hay nada "de hackathon" en esta elección. |
| **Obtención de datos** | `fetch` directo en Server Components, sin librería de estado del lado cliente (sin SWR/React Query/Redux) | Con `cache:"no-store"` en cada llamada, cada carga de página ya trae datos frescos del backend — no hay estado de cliente que sincronizar porque casi no hay estado de cliente. Para las ~3 pantallas con interacción real (selección de facturas, el chat de IA) un `useState` normal alcanza. | Frente a SWR/React Query: cero dependencias, cero configuración de caché para invalidar — en una app donde cada pantalla muestra dinero real, "siempre pedir de nuevo" es más simple de razonar que una caché que hay que invalidar correctamente. | **Sí, con un matiz.** Para un producto con mucho más tráfico, se agregaría caché explícita (revalidación por tiempo o por tag de Next.js) en los endpoints que no cambian a cada segundo — hoy todo pide datos frescos siempre, lo cual es correcto pero no la opción más barata en cómputo del backend a gran escala. |
| **Estilos** | Tailwind CSS (config CSS-first, sin `tailwind.config.js`) | Se construyeron decenas de pantallas con un lenguaje visual consistente (colores, espaciados) rápido, sin diseñar un sistema de componentes propio desde cero para un hackathon. | Frente a CSS Modules/styled-components: cero archivos de estilos por componente que mantener sincronizados; los tokens de marca (`--color-navy`, `--color-lime`, etc.) viven en un solo lugar (`globals.css`). | **Sí.** Tailwind es una elección de producción común. Lo único a revisar antes de escalar el equipo: extraer patrones repetidos (tarjetas, botones) a componentes reutilizables — hoy hay bastante className repetido entre pantallas similares. |
| **Autenticación / roles** | Cookie httpOnly con un valor de rol (`sme`/`financier`), sin usuarios reales ni contraseñas | El objetivo del demo era mostrar ambas experiencias (empresa y financiadora) sin construir un sistema de autenticación completo bajo presión de tiempo de hackathon. | Frente a implementar auth real (NextAuth, Clerk, Auth0): cero tiempo invertido en un sistema que no era el punto a demostrar. | **No.** Esto es explícitamente no apto para producción — no hay verificación de identidad, cualquiera puede "ser" cualquier rol. Antes de un lanzamiento real hace falta autenticación real (NextAuth.js o un proveedor gestionado), sesiones ligadas a una cuenta real en el backend, y el flujo de onboarding de `/register` conectado a verificación real de documentos (hoy no sube ni guarda nada). |
| **Chat de IA en el navegador** | `react-markdown` + `remark-gfm`, llamando al backend directo desde el cliente (única excepción al patrón de Server Components) | El chat necesita turnos interactivos en tiempo real — no tiene sentido como Server Component. `NEXT_PUBLIC_API_URL` ya es pública, así que llamar al backend directo desde el navegador no expone nada que no estuviera expuesto ya. | Frente a escribir un parser de Markdown propio: la librería maneja tablas, listas anidadas y casos borde de Markdown que el modelo genera de formas impredecibles — reescribir eso a mano hubiera sido tiempo perdido. | **Sí para el patrón, con revisión de UX en producción**: en un producto real probablemente se querría streaming de la respuesta (hoy se espera la respuesta completa) y un límite de longitud de conversación visible para el usuario. |
| **Despliegue** | Vercel | Es la plataforma con menos fricción para desplegar Next.js (literalmente hecha por el mismo equipo) — cada push a `main` se despliega solo, con preview deployments por PR gratis. | Frente a desplegar Next.js en la misma VPS que el backend: Vercel da CDN global, rollbacks con un clic, y logs de runtime por request sin configurar nada — todo lo cual usamos activamente para diagnosticar errores durante este proyecto. | **Sí.** Es una elección de producción real y común para apps Next.js — no hay que migrar de plataforma para escalar esto. |
