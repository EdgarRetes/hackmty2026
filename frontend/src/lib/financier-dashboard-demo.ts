// Temporary visualization-only data. Replace these exports when the API exposes
// financier-scoped capital history and portfolio risk allocation.
export const DEMO_CAPITAL_HISTORY = [
  { label: "Abr", amountCents: 36_000_000 },
  { label: "May", amountCents: 68_000_000 },
  { label: "Jun", amountCents: 94_000_000 },
  { label: "Jul", amountCents: 118_000_000 },
  { label: "Ago", amountCents: 137_000_000 },
  { label: "Sep", amountCents: 172_000_000 },
] as const;

export const DEMO_PORTFOLIO_BY_RISK = [
  { label: "Riesgo bajo", percentage: 68, amountCents: 465_120_000, color: "#2db766", dotClass: "bg-emerald-500" },
  { label: "Riesgo medio", percentage: 25, amountCents: 171_000_000, color: "#ffb51b", dotClass: "bg-amber-400" },
  { label: "Riesgo alto", percentage: 7, amountCents: 47_880_000, color: "#f04444", dotClass: "bg-red-500" },
] as const;

export const DEMO_PORTFOLIO_TOTAL_CENTS = DEMO_PORTFOLIO_BY_RISK.reduce((total, item) => total + item.amountCents, 0);
