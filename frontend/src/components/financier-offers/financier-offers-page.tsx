"use client";

import { useMemo, useState } from "react";
import type { FinancierOffer, FinancierOffersData, FinancierOfferStatus } from "@/lib/financier-offers";
import { formatCents } from "@/lib/marketplace";
import { Icon, type IconName } from "../icons";

const PAGE_SIZE = 8;
type Filter = "all" | FinancierOfferStatus;
const filters: { value: Filter; label: string }[] = [{ value: "all", label: "Todas" }, { value: "pending", label: "Pendientes" }, { value: "accepted", label: "Aceptadas" }, { value: "rejected", label: "Rechazadas" }, { value: "expired", label: "Expiradas" }];

export function FinancierOffersPageContent({ data }: { data: FinancierOffersData }) {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<Filter>("all");
  const [page, setPage] = useState(1);
  const filtered = useMemo(() => data.offers.filter((offer) => {
    const needle = query.trim().toLocaleLowerCase("es-MX");
    return (!needle || offer.invoiceFolio.toLocaleLowerCase("es-MX").includes(needle) || offer.debtor.toLocaleLowerCase("es-MX").includes(needle)) && (filter === "all" || offer.status === filter);
  }).sort((a, b) => b.offeredAt.localeCompare(a.offeredAt)), [data.offers, filter, query]);
  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, pageCount);
  const visible = filtered.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE);
  function changeFilter(next: Filter) { setFilter(next); setPage(1); }

  return <div className="mx-auto max-w-[1380px]"><header><h1 className="text-[38px] font-bold leading-none tracking-[-.04em] text-navy">Ofertas</h1><p className="mt-2 text-[17px] text-[#1d54b7]">Consulta el estado de las ofertas que has enviado.</p></header><section className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-5"><OfferKpi label="Total de ofertas" value={data.totals.all} detail="Ofertas enviadas" icon="invoice" tone="blue"/><OfferKpi label="Pendientes" value={data.totals.pending} detail="Esperando respuesta" icon="clock" tone="orange"/><OfferKpi label="Aceptadas" value={data.totals.accepted} detail="Convertidas en financiamientos" icon="check" tone="green"/><OfferKpi label="Rechazadas" value={data.totals.rejected} detail="No fueron seleccionadas" icon="compare" tone="red"/><OfferKpi label="Expiradas" value={data.totals.expired} detail="Ya no están vigentes" icon="clock" tone="gray"/></section><section className="mt-4 overflow-hidden rounded-xl border border-slate-200 bg-white p-5 shadow-[0_8px_24px_rgba(15,31,68,.025)]"><div className="flex flex-wrap items-start justify-between gap-4"><div><h2 className="text-xl font-bold text-navy">Tus ofertas</h2><p className="mt-1 text-sm text-[#52688f]">Historial de ofertas enviadas a través de la plataforma.</p></div><div className="flex flex-wrap gap-3"><label className="flex h-11 min-w-[300px] items-center gap-3 rounded-xl bg-[#f1f5fa] px-4 text-[#52688f]"><Icon name="search" size={19}/><input value={query} onChange={(event) => { setQuery(event.target.value); setPage(1); }} placeholder="Buscar factura o deudor..." className="w-full bg-transparent text-sm text-navy outline-none placeholder:text-[#6b7fa5]"/></label><span className="flex h-11 items-center gap-3 rounded-xl border border-slate-200 px-4 text-sm font-medium text-navy">Más recientes <Icon name="chevron" size={16}/></span></div></div><div className="mt-4 flex flex-wrap gap-2">{filters.map((item) => <button key={item.value} type="button" onClick={() => changeFilter(item.value)} className={`rounded-full px-5 py-2 text-sm font-medium ${filter === item.value ? "bg-[#1764ed] text-white" : "bg-[#f0f4fa] text-[#38517d]"}`}>{item.label} ({data.totals[item.value] ?? "—"})</button>)}</div><div className="mt-4">{visible.length ? <OffersTable offers={visible}/> : <div className="py-16 text-center"><h3 className="text-lg font-semibold text-navy">Aún no hay ofertas disponibles.</h3><p className="mt-2 text-sm text-[#52688f]">{data.collectionAvailable ? "No hay resultados que coincidan con los filtros." : "El backend todavía no expone el historial de ofertas del financiador."}</p></div>}</div><footer className="flex min-h-12 flex-wrap items-center justify-between gap-3 border-t border-slate-200 pt-4 text-xs text-[#1d54b7]"><span>Mostrando {filtered.length ? (safePage-1)*PAGE_SIZE+1 : 0}–{Math.min(safePage*PAGE_SIZE, filtered.length)} de {filtered.length} resultados</span><div className="flex gap-1">{Array.from({ length: pageCount }, (_, index) => index + 1).map((number) => <button key={number} type="button" onClick={() => setPage(number)} className={`h-8 min-w-8 rounded-lg ${number === safePage ? "bg-[#e8f1ff] font-semibold text-[#1764ed]" : "text-navy"}`}>{number}</button>)}</div></footer></section></div>;
}

function OffersTable({ offers }: { offers: FinancierOffer[] }) {
  return <div className="overflow-x-auto"><table className="w-full min-w-[1120px] border-collapse text-left"><thead className="bg-[#f1f5fa] text-xs text-[#38517d]"><tr>{["Factura", "Deudor", "Monto de la factura", "Tu oferta", "Retorno ofrecido", "Fecha de oferta", "Estado", "Acción"].map((label) => <th key={label} className="px-3 py-3 font-medium">{label}</th>)}</tr></thead><tbody>{offers.map((offer) => <tr key={offer.id} className="border-t border-slate-200 text-[13px] text-navy"><td className="px-3 py-3 font-semibold">{offer.invoiceFolio}</td><td className="px-3 py-3">{offer.debtor}</td><td className="px-3 py-3">{formatCents(offer.invoiceAmountCents)} MXN</td><td className="px-3 py-3 font-semibold">{formatCents(offer.offeredAmountCents)} MXN</td><td className="px-3 py-3">{offer.offeredReturnRate}%</td><td className="px-3 py-3">{formatDate(offer.offeredAt)}</td><td className="px-3 py-3"><StatusBadge status={offer.status}/></td><td className="px-3 py-3"><span className="inline-flex rounded-lg bg-[#f1f6ff] px-4 py-2 text-xs font-semibold text-[#075ad9]" title="La ruta de detalle aún no está disponible">Ver detalles</span></td></tr>)}</tbody></table></div>;
}

function OfferKpi({ label, value, detail, icon, tone }: { label: string; value: number | null; detail: string; icon: IconName; tone: "blue" | "orange" | "green" | "red" | "gray" }) {
  const colors = { blue: "bg-blue-50 text-blue-600", orange: "bg-orange-50 text-orange-500", green: "bg-emerald-50 text-emerald-600", red: "bg-red-50 text-red-500", gray: "bg-slate-100 text-slate-500" };
  return <article className="flex min-h-[116px] gap-3 rounded-xl border border-slate-200 bg-white p-4"><span className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl ${colors[tone]}`}><Icon name={icon} size={25}/></span><div><p className="text-xs text-[#38517d]">{label}</p><strong className="mt-1 block text-[24px] leading-none text-navy">{value ?? "—"}</strong><p className="mt-2 text-[11px] leading-4 text-[#52688f]">{detail}</p></div></article>;
}

function StatusBadge({ status }: { status: FinancierOfferStatus }) {
  const styles = { pending: "bg-orange-50 text-orange-600", accepted: "bg-emerald-50 text-emerald-700", rejected: "bg-red-50 text-red-600", expired: "bg-slate-100 text-slate-600" };
  const labels = { pending: "Pendiente", accepted: "Aceptada", rejected: "Rechazada", expired: "Expirada" };
  return <span className={`inline-flex rounded-lg px-3 py-1.5 text-xs ${styles[status]}`}>{labels[status]}</span>;
}

function formatDate(value: string): string { return new Intl.DateTimeFormat("es-MX", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(value)); }
