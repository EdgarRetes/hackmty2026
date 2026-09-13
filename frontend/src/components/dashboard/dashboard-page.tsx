import type { DashboardData } from "@/lib/dashboard";
import { formatMoney } from "@/lib/dashboard";
import { DashboardKpiCard } from "./dashboard-kpi-card";
import { FactoraImpact } from "./factora-impact";
import { LiquidityProjection } from "./liquidity-projection";
import { OpportunitiesPanel } from "./opportunities-panel";
import { RecentActivity } from "./recent-activity";

export function DashboardPage({ data }: { data: DashboardData }) {
  const date = new Intl.DateTimeFormat("es-MX", { day: "numeric", month: "long", year: "numeric", timeZone: "America/Mexico_City" }).format(new Date());
  return <div className="mx-auto max-w-[1380px]"><header className="flex flex-wrap items-start justify-between gap-3"><div><h1 className="text-[36px] font-bold leading-none tracking-[-.04em] text-navy">Buenos días, Lucía</h1><p className="mt-2 text-[16px] text-[#52688f]">Este es el estado financiero de tu empresa hoy.</p></div><time className="pt-1 text-sm text-[#52688f]">{date}</time></header><section className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4"><DashboardKpiCard label="Cuentas por cobrar" value={formatMoney(data.receivablesAmount)} detail={`${data.receivablesCount} facturas pendientes`} icon="invoice" tone="navy"/><DashboardKpiCard label="Disponible para financiar" value={formatMoney(data.eligibleAmount)} detail={`${data.eligibleCount} facturas elegibles`} icon="coins" tone="green"/><DashboardKpiCard label="Ofertas activas" value={data.activeOffers === null ? "—" : String(data.activeOffers)} detail={data.invoicesWithActiveOffers === null ? "Información no disponible" : `En ${data.invoicesWithActiveOffers} facturas`} icon="bars" tone="purple"/><DashboardKpiCard label="Capital financiado" value={formatMoney(data.financedAmount)} detail={`${data.financedCount} facturas financiadas`} icon="check" tone="green"/></section><div className="mt-4 grid gap-4 xl:grid-cols-[1.55fr_1fr]"><LiquidityProjection/><OpportunitiesPanel opportunities={data.opportunities}/></div><div className="mt-4 grid gap-4 xl:grid-cols-[1.55fr_1fr]"><RecentActivity invoices={data.invoices}/><FactoraImpact financedAmount={data.financedAmount}/></div></div>;
}
