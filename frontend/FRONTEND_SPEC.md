# Factora Frontend Specification

## 1. Product Overview

Factora is an invoice-financing marketplace for SMEs.

The platform allows an SME to:

1. View its outstanding invoices.
2. Select an invoice that needs liquidity.
3. Receive financing offers from multiple financiers.
4. Compare those offers.
5. Select the most convenient option.
6. Track active financing and transactions.

The frontend communicates with a Django REST API, but during the initial frontend implementation, local mock data should be used.

---

# 2. Design System

## Visual Direction

Factora should feel like a modern financial SaaS product:

- Professional
- Trustworthy
- Clean
- Modern
- Easy to understand
- Visually distinctive without feeling informal

Avoid excessive gradients, decorative graphics, or unnecessary visual noise.

The interface should use generous whitespace, rounded cards, subtle borders, and restrained shadows.

## Visual References

Primary marketplace reference:

`references/offers-marketplace.png`

Color system reference:

`references/color-palette.png`

The implementation should follow these references closely.

The marketplace image defines:

- Overall layout
- Sidebar proportions
- Top navigation
- Card layout
- Information hierarchy
- Spacing
- Offer differentiation
- General visual language

The color palette image defines the intended semantic color system.

---

# 3. Global Application Layout

The application uses a persistent left sidebar and a top bar.

## Sidebar

Brand:

`Factora`

Tagline:

`Financiamiento que impulsa.`

Main navigation:

- Home
- Facturas
- Ofertas
- Financiamientos
- Transacciones

Secondary navigation:

- Configuración
- Ayuda

The currently active section should use a soft lime background.

Use simple outline-style icons.

The sidebar should preserve the decorative visual element shown in:

`references/offers-marketplace.png`

The decoration is visual only and should not behave as a button.

## Top Bar

The top bar contains:

- Search field
- Notification icon
- User avatar
- User name
- Company name

Mock user:

Name:
`Lucía Martínez`

Company:
`Industrias Monterrey`

Search placeholder:

`Buscar facturas, clientes...`

---

# 4. Offers Page

## Route

`/offers/[invoiceId]`

Example:

`/offers/INV-1842`

This is the core marketplace experience of Factora.

Use:

`references/offers-marketplace.png`

as the primary visual reference.

---

# 5. Page Header

Title:

`Ofertas`

Subtitle:

`Compara las mejores opciones de financiamiento para tu factura.`

---

# 6. Invoice Summary

Display a summary card above the offers.

Mock invoice:

Invoice ID:
`#INV-1842`

Status:
`Verificada`

Client:
`Nemak México`

Invoice amount:
`$500,000 MXN`

Due date:
`29 oct 2026`

Days remaining:
`47 días`

The verified state should use a subtle success-green badge.

Do NOT display debtor risk information on the Offers page.

Do NOT display a workflow stepper or progress bar.

---

# 7. Offer Sorting

Above the offer cards, display:

`Ordenar por`

Available options:

- Mejor oferta para ti
- Menor comisión
- Mayor anticipo
- Más rápido

The active option should be visually obvious.

Default:

`Mejor oferta para ti`

For the initial mock implementation, these controls should update the selected state visually.

If simple client-side sorting can be implemented without unnecessary complexity, it may also reorder the mock offers.

---

# 8. Compare Offers

Display a secondary control:

`Comparar ofertas (0)`

The full comparison experience is outside the scope of the first implementation.

The control should exist visually but does not need complete comparison logic yet.

---

# 9. Offer Cards

Display four financing offers.

All cards should share the same component structure.

Each offer must display:

- Financier name or logo
- Offer category badge when applicable
- Amount the SME will receive
- Advance percentage
- Commission percentage
- Financing cost
- Funding time
- Primary action
- Short explanation

Cards should remain primarily white.

Semantic colors should be used through:

- Borders
- Badges
- Icons
- CTA backgrounds
- Small informational areas

Do not fill the entire card with strong colors.

---

# 10. Mock Offers

## Offer 1 — Capital One

Financier:
`Capital One`

Category:
`Mejor oferta`

Amount received:
`$472,500 MXN`

Advance:
`95%`

Commission:
`2.1%`

Financing cost:
`$10,500 MXN`

Funding:
`Hoy mismo`

Primary CTA:
`Aceptar oferta`

Explanation:

`Esta es la mejor oferta para ti por su balance entre costo, rapidez y monto de anticipo.`

Semantic color:
Lime

This is the recommended offer and should have the strongest visual hierarchy.

---

## Offer 2 — Factor MX

Financier:
`Factor MX`

Category:
`Menor comisión`

Amount received:
`$468,200 MXN`

Advance:
`94%`

Commission:
`1.8%`

Financing cost:
`$9,000 MXN`

Funding:
`24 horas`

Primary CTA:
`Ver detalles`

Explanation:

`La opción con la comisión más baja.`

Semantic color:
Blue

---

## Offer 3 — Global Finance

Financier:
`Global Finance`

Category:
`Mayor anticipo`

Amount received:
`$475,000 MXN`

Advance:
`97%`

Commission:
`3.4%`

Financing cost:
`$17,000 MXN`

Funding:
`48 horas`

Primary CTA:
`Ver detalles`

Explanation:

`El mayor porcentaje de anticipo de todas las ofertas.`

Semantic color:
Purple

---

## Offer 4 — Novus Capital

Financier:
`Novus Capital`

Category:
`Más rápido`

Amount received:
`$465,000 MXN`

Advance:
`93%`

Commission:
`2.8%`

Financing cost:
`$14,000 MXN`

Funding:
`24 horas`

Primary CTA:
`Ver detalles`

Explanation:

`Una excelente opción si necesitas liquidez en el corto plazo.`

Semantic color:
Orange

---

# 11. Semantic Colors

Use `references/color-palette.png` as the visual source of truth.

Conceptually:

## Navy

Used for:

- Main headings
- Important financial values
- Navigation icons
- Primary typography

## Lime

Used for:

- Factora primary accent
- Recommended offer
- Primary CTA
- Active navigation
- Important highlights

## Blue

Used for:

- Lowest commission offer

## Purple

Used for:

- Highest advance offer

## Orange

Used for:

- Fastest funding offer

## Green

Reserved for success states such as:

- Verified invoice
- Successful operation

Do not use semantic colors arbitrarily.

---

# 12. Bottom Information Panel

Below the offers, display an informational panel.

Title:

`¿Cómo elegimos estas ofertas?`

Description:

`Nuestro algoritmo analiza el monto de tu factura, el tiempo de vencimiento y las condiciones de cada financiadora para mostrarte las mejores opciones.`

CTA:

`Conocer más`

For the first implementation, this CTA does not need a complete destination.

---

# 13. Components

Do not implement the entire interface as one large page component.

Prefer reusable components such as:

- `AppSidebar`
- `TopBar`
- `InvoiceSummary`
- `OfferFilters`
- `OfferCard`
- `OffersGrid`
- `OffersExplanation`

Exact filenames and internal organization may follow the existing project structure and current Next.js conventions.

Offer data should be separated from the visual card component.

The same `OfferCard` component should render all four offers using props/data.

---

# 14. Mock Data

For this first implementation:

- Use local mock data.
- Do not call the Django API.
- Do not implement financial calculations in the frontend.
- Values displayed in the UI should come from mock offer objects.

The backend will eventually be responsible for:

- Risk analysis
- Pricing
- Advance calculation
- Commission calculation
- Financing cost
- Offer ranking
- Recommended offer selection

The frontend should eventually consume these results through the REST API.

---

# 15. Interactions for First Implementation

Required:

- Sidebar active state
- Offer sorting control active state
- Hover states
- Button states
- Basic responsive behavior

Not required yet:

- Real authentication
- Real notifications
- Backend API calls
- Real payment processing
- Full offer comparison
- Real search
- Real financial calculations

The `Aceptar oferta` and `Ver detalles` buttons may use simple placeholder behavior for this iteration.

---

# 16. Responsive Behavior

Primary target:

Desktop web application.

The approved desktop reference should be prioritized.

On narrower screens:

- Cards may wrap into fewer columns.
- Sidebar behavior may adapt as necessary.
- Content must remain readable.
- Financial values must not overflow cards.

Do not sacrifice the desktop design in order to over-engineer mobile behavior during the hackathon.

---

# 17. Scope of First Implementation

The first implementation should build ONLY:

- Global application shell required for the Offers page
- Sidebar
- Top bar
- Offers page
- Invoice summary
- Filters
- Four offer cards
- Bottom explanation panel

Do NOT implement the full:

- Home page
- Invoices page
- Financing page
- Transactions page
- Settings page
- Help page

Those sections may appear in navigation but can remain non-functional placeholders for now.

---

# 18. Acceptance Criteria

The task is complete when:

1. `/offers/INV-1842` renders successfully.
2. The page closely resembles `references/offers-marketplace.png`.
3. The semantic colors resemble `references/color-palette.png`.
4. The left sidebar is present.
5. The top bar is present.
6. The invoice summary displays the specified mock invoice.
7. Four offer cards render from reusable data/components.
8. Capital One is visually identified as the recommended offer.
9. The four semantic offer categories are visually distinguishable.
10. No debtor-risk section is displayed.
11. No workflow stepper is displayed.
12. No Django/backend integration is introduced.
13. The page is usable at common desktop resolutions.
14. Lint passes.
15. Production build passes.