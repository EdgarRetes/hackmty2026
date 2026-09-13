"use client";

import { useMemo, useState } from "react";
import { formatFinancingMoney, type FinancingListItem, type FinancingUiStatus } from "@/lib/financing";
import { Icon } from "../icons";
import { FinancingSummaryCard } from "./financing-summary-card";
import { FinancingTable } from "./financing-table";

const PAGE_SIZE = 8;
const filters: { label: string; value: "all" | FinancingUiStatus }[] = [
  { label: "Todas", value: "all" },
  { label: "Activos", value: "active" },
  { label: "Completados", value: "completed" },
  { label: "Cancelados", value: "cancelled" },
];

export function FinancingPageContent({ financings }: { financings: FinancingListItem[] }) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<"all" | FinancingUiStatus>("all");
  const [page, setPage] = useState(1);
  const activeFinancings = useMemo(() => financings.filter((item) => item.status === "active"), [financings]);
  const completedFinancings = useMemo(() => financings.filter((item) => item.status === "completed"), [financings]);
  const capitalReceived = useMemo(() => financings.reduce((sum, item) => sum + item.receivedAmount, 0), [financings]);
  const activeAmount = useMemo(() => activeFinancings.reduce((sum, item) => sum + item.receivedAmount, 0), [activeFinancings]);
  const completedAmount = useMemo(() => completedFinancings.reduce((sum, item) => sum + item.receivedAmount, 0), [completedFinancings]);
  const filtered = useMemo(() => financings.filter((item) => {
    const needle = query.trim().toLocaleLowerCase("es-MX");
    const matchesStatus = status === "all" || item.status === status;
    return matchesStatus && (!needle || item.invoiceFolio.toLocaleLowerCase("es-MX").includes(needle) || item.lender.toLocaleLowerCase("es-MX").includes(needle));
  }), [financings, query, status]);
  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, pageCount);
  const visible = filtered.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE);
  const start = filtered.length ? (safePage - 1) * PAGE_SIZE + 1 : 0;
  const end = Math.min(safePage * PAGE_SIZE, filtered.length);

  function updateQuery(value: string) { setQuery(value); setPage(1); }
  function updateStatus(value: "all" | FinancingUiStatus) { setStatus(value); setPage(1); }

  return <div className="mx-auto max-w-[1380px]"><h1 className="text-[38px] font-bold leading-none tracking-[-.04em] text-navy">Financiamientos</h1><p className="mt-1.5 text-[17px] text-[#52688f]">Consulta el estado y avance de tus financiamientos.</p>
    <section className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4"><FinancingSummaryCard label="Financiamientos activos" value={String(activeFinancings.length)} detail={`${formatFinancingMoney(activeAmount)} en curso`} tone="blue" icon="cube"/><FinancingSummaryCard label="Capital recibido" value={formatFinancingMoney(capitalReceived)} detail={`${financings.length} financiamientos`} tone="green" icon="coins"/><FinancingSummaryCard label="Por liquidar" value="—" detail="Saldo no disponible" tone="purple" icon="clock"/><FinancingSummaryCard label="Financiamientos completados" value={String(completedFinancings.length)} detail={`${formatFinancingMoney(completedAmount)} en total`} tone="green" icon="check"/></section>
    <section className="mt-5 flex flex-wrap items-center gap-2.5"><label className="flex h-11 min-w-[300px] flex-1 items-center gap-3 rounded-xl border border-slate-200 bg-[#f6f8fb] px-4 text-[#52688f] xl:max-w-[435px]"><Icon name="search" size={20}/><input value={query} onChange={(event) => updateQuery(event.target.value)} className="w-full bg-transparent text-sm text-navy outline-none placeholder:text-[#6b7fa5]" placeholder="Buscar por factura o financiadora..."/></label>{filters.map((filter) => <button key={filter.value} type="button" onClick={() => updateStatus(filter.value)} className={`h-11 rounded-full border px-6 text-sm transition ${status === filter.value ? "border-navy bg-navy text-white shadow-sm" : "border-slate-200 bg-white text-[#38517d] hover:border-slate-400"}`}>{filter.label}</button>)}<button type="button" className="ml-auto flex h-11 items-center gap-3 rounded-xl border border-slate-200 bg-white px-5 text-sm font-medium text-navy"><Icon name="transfer" size={18}/>Más recientes <Icon name="chevron" size={16}/></button></section>
    <section className="mt-5 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-[0_8px_24px_rgba(15,31,68,.025)]">{visible.length ? <FinancingTable financings={visible}/> : <EmptyState filtered={Boolean(query.trim()) || status !== "all"}/>}<footer className="flex min-h-16 flex-wrap items-center justify-between gap-4 border-t border-slate-200 px-5 py-3 text-xs text-[#52688f]"><span>Mostrando {start}–{end} de {filtered.length} financiamientos</span><div className="flex items-center gap-1"><PageButton label="Anterior" disabled={safePage === 1} onClick={() => setPage((current) => Math.max(1, current - 1))}>‹</PageButton>{Array.from({ length: pageCount }, (_, index) => index + 1).map((number) => <PageButton key={number} label={`Página ${number}`} active={number === safePage} onClick={() => setPage(number)}>{number}</PageButton>)}<PageButton label="Siguiente" disabled={safePage === pageCount} onClick={() => setPage((current) => Math.min(pageCount, current + 1))}>›</PageButton></div></footer></section>
  </div>;
}

function EmptyState({ filtered }: { filtered: boolean }) {
  return <div className="px-6 py-16 text-center"><h2 className="text-lg font-semibold text-navy">{filtered ? "No encontramos financiamientos." : "Aún no tienes financiamientos."}</h2><p className="mt-2 text-sm text-[#52688f]">{filtered ? "Prueba cambiando la búsqueda o el filtro seleccionado." : "Cuando aceptes una oferta, aparecerá aquí."}</p></div>;
}

function PageButton({ children, label, active, disabled, onClick }: { children: React.ReactNode; label: string; active?: boolean; disabled?: boolean; onClick: () => void }) {
  return <button type="button" aria-label={label} disabled={disabled} onClick={onClick} className={`flex h-8 min-w-8 items-center justify-center rounded-lg px-2 transition disabled:opacity-30 ${active ? "bg-slate-100 font-semibold text-navy" : "hover:bg-slate-50"}`}>{children}</button>;
}
