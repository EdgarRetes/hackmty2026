import Link from "next/link";
import { formatCents, type MarketplaceOpportunity } from "@/lib/marketplace";
import type { CapitalHistoryPoint, PortfolioByRisk, RecentOperation } from "@/lib/financier-dashboard";
import { Icon } from "../icons";

const STATUS_LABELS: Record<RecentOperation["status"], string> = {
  pending: "Pendiente",
  in_auction: "En subasta",
  funded: "Activo",
  paid: "Completado",
  overdue: "Vencido",
};

export function CapitalChart({ history }: { history: CapitalHistoryPoint[] | null }) {
  const max = history ? Math.max(1, ...history.map((point) => point.amountCents)) : 1;
  const points = history?.map((point, index) => ({ x: 60 + index * (500 / Math.max(1, history.length - 1)), y: 175 - (point.amountCents / max) * 140 })) ?? [];
  return <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-[0_8px_24px_rgba(15,31,68,.025)]"><PanelHeading title="Capital financiado" subtitle="Evolución de tu portafolio en los últimos meses"/>{history && history.some((point) => point.amountCents > 0) ? <div className="mt-4 overflow-x-auto"><svg viewBox="0 0 620 215" className="h-[205px] min-w-[560px] w-full" role="img" aria-label="Capital financiado durante los últimos seis meses"><g stroke="#e6edf6">{[35, 80, 125, 175].map((y) => <line key={y} x1="42" x2="590" y1={y} y2={y}/>)}</g>{history.map((point, index) => <g key={point.month}><rect x={points[index].x-17} y={points[index].y} width="34" height={175-points[index].y} rx="7" fill="#cfe3ff"><title>{formatCents(point.amountCents)}</title></rect><text x={points[index].x} y="201" textAnchor="middle" fill="#3762ac" fontSize="11">{point.label}</text></g>)}<polyline points={points.map((point) => `${point.x},${point.y}`).join(" ")} fill="none" stroke="#f59e0b" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/><g fill="#f59e0b" stroke="white" strokeWidth="2">{points.map((point, index) => <circle key={index} cx={point.x} cy={point.y} r="5.5"/>)}</g></svg></div> : <div className="relative mt-5 h-[205px] overflow-hidden border-b border-l border-slate-200 bg-[repeating-linear-gradient(to_bottom,transparent_0,transparent_49px,#e8eef7_50px)]"><div className="absolute inset-0 flex items-center justify-center"><Empty label="Aún no tienes financiamientos en los últimos 6 meses"/></div></div>}</section>;
}

export function Opportunities({ opportunities }: { opportunities: MarketplaceOpportunity[] }) {
  return <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-[0_8px_24px_rgba(15,31,68,.025)]"><div className="flex items-start justify-between gap-3"><PanelHeading title="Oportunidades para ti" subtitle="Facturas disponibles en el Marketplace"/><Link href="/marketplace" className="flex h-9 shrink-0 items-center gap-2 rounded-lg bg-[#f3f6fb] px-4 text-xs font-semibold text-[#075ad9]">Ver todas <Icon name="arrow" size={16}/></Link></div><div className="mt-3 divide-y divide-slate-100">{opportunities.length ? opportunities.map((item) => <article key={item.id} className="grid grid-cols-[46px_1fr_auto] items-center gap-3 py-3"><span className="flex h-11 w-11 items-center justify-center rounded-lg border border-slate-200 bg-white text-xs font-bold text-[#1d54b7]">{item.debtorInitials}</span><div className="min-w-0"><strong className="block truncate text-sm text-navy">{item.debtor}</strong><span className="mt-1 block text-xs text-[#1d54b7]">{item.formattedAmount}</span><span className="mt-1 block text-[11px] text-[#6b7fa5]">Riesgo {riskLabel(item.risk)} · Retorno {item.estimatedReturnRate === null ? "—" : `${item.estimatedReturnRate}%`} · {item.previouslyFinanced ? "Deudor conocido" : "Nuevo deudor"}</span></div><Link href={`/marketplace/${item.id}`} className="rounded-lg border border-[#dce7fa] bg-[#f7faff] px-3 py-2 text-xs font-semibold text-[#075ad9] transition hover:bg-[#eef4ff]">Ver oportunidad</Link></article>) : <Empty label="No hay oportunidades disponibles"/>}</div></section>;
}

export function RecentOperations({ operations }: { operations: RecentOperation[] | null }) {
  return <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-[0_8px_24px_rgba(15,31,68,.025)]"><div className="flex items-start justify-between gap-3"><PanelHeading title="Operaciones recientes" subtitle="Tus últimos financiamientos y su estado"/><Link href="/portfolio" className="flex h-9 shrink-0 items-center gap-2 rounded-lg bg-[#f3f6fb] px-4 text-xs font-semibold text-[#075ad9]">Ver portafolio <Icon name="arrow" size={16}/></Link></div><div className="mt-4 overflow-hidden rounded-lg border border-slate-100"><div className="grid grid-cols-6 bg-[#f3f6fb] px-3 py-2 text-[11px] text-[#38517d]"><span>Factura</span><span>Deudor</span><span>Capital</span><span>Plazo</span><span>Estado</span><span>Retorno</span></div>{operations && operations.length ? <div className="divide-y divide-slate-100">{operations.map((operation) => <div key={operation.invoiceFolio + operation.debtor} className="grid grid-cols-6 items-center px-3 py-2.5 text-[12px] text-navy"><span className="font-semibold">{operation.invoiceFolio}</span><span className="truncate">{operation.debtor}</span><span>{operation.formattedCapital}</span><span>{operation.termDays} días</span><span>{STATUS_LABELS[operation.status]}</span><span>{operation.formattedReturn}</span></div>)}</div> : <div className="py-12"><Empty label="No hay operaciones disponibles para esta cuenta"/></div>}</div></section>;
}

export function PortfolioDistribution({ byRisk }: { byRisk: PortfolioByRisk | null }) {
  const total = byRisk ? byRisk.low + byRisk.medium + byRisk.high : 0;
  const risks = [
    ["Riesgo bajo", "bg-emerald-500", byRisk?.low ?? 0] as const,
    ["Riesgo medio", "bg-amber-400", byRisk?.medium ?? 0] as const,
    ["Riesgo alto", "bg-red-500", byRisk?.high ?? 0] as const,
  ];
  const low = total ? (risks[0][2] / total) * 100 : 0;
  const medium = total ? (risks[1][2] / total) * 100 : 0;
  const donut = total ? `conic-gradient(#10b981 0 ${low}%, #fbbf24 ${low}% ${low + medium}%, #ef4444 ${low + medium}% 100%)` : "#edf1f6";
  return <section id="portfolio" className="scroll-mt-24 rounded-xl border border-slate-200 bg-white p-5 shadow-[0_8px_24px_rgba(15,31,68,.025)]"><PanelHeading title="Distribución de tu portafolio" subtitle="Capital financiado por nivel de riesgo"/><div className="mt-5 flex min-h-[205px] flex-wrap items-center justify-around gap-8"><div className="flex h-[184px] w-[184px] shrink-0 items-center justify-center rounded-full" style={{ background: donut }}><div className="flex h-[132px] w-[132px] flex-col items-center justify-center rounded-full bg-white px-2 text-center"><strong className="whitespace-nowrap text-[16px] leading-none text-navy">{total > 0 ? formatCents(total).replace(/\.00$/, "") : "—"}</strong><span className="mt-2 text-[11px] font-medium leading-none text-[#52688f]">MXN</span></div></div><div className="min-w-[210px] space-y-5">{risks.map(([label, color, amountCents]) => <div key={label} className="grid grid-cols-[14px_1fr_auto] items-center gap-3"><i className={`h-3.5 w-3.5 rounded-full ${color}`}/><span className="text-sm text-navy">{label}</span><strong className="text-sm text-navy">{total > 0 ? `${Math.round((amountCents / total) * 100)}%` : "—"}</strong><span/><span className="text-xs text-[#1d54b7]">{total > 0 ? `${formatCents(amountCents)} MXN` : "— MXN"}</span></div>)}</div></div></section>;
}

function riskLabel(risk: MarketplaceOpportunity["risk"]): string {
  if (risk === "low") return "bajo";
  if (risk === "medium") return "medio";
  if (risk === "high") return "alto";
  return "—";
}

function PanelHeading({ title, subtitle }: { title: string; subtitle: string }) { return <div><h2 className="text-xl font-bold tracking-[-.025em] text-navy">{title}</h2><p className="mt-0.5 text-xs text-[#1d54b7]">{subtitle}</p></div>; }
function Empty({ label }: { label: string }) { return <p className="px-4 py-6 text-center text-sm text-[#6b7fa5]">{label}</p>; }
