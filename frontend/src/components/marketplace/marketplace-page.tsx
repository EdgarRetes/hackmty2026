"use client";

import { useMemo, useState } from "react";
import { formatCents, type MarketplaceData, type MarketplaceOpportunity, type MarketplaceRisk } from "@/lib/marketplace";
import { Icon } from "../icons";
import { MarketplaceKpiCard } from "./marketplace-kpi-card";
import { MarketplaceTable } from "./marketplace-table";

const PAGE_SIZE = 8;
type QuickFilter = "all" | "known" | MarketplaceRisk;
type AmountFilter = "all" | "under_100" | "100_500" | "over_500";
type TermFilter = "all" | "under_30" | "30_60" | "over_60";
type Sort = "newest" | "amount_desc" | "amount_asc";

export function MarketplacePageContent({ data }: { data: MarketplaceData }) {
  const [query, setQuery] = useState("");
  const [quickFilter, setQuickFilter] = useState<QuickFilter>("all");
  const [sectorFilter, setSectorFilter] = useState("all");
  const [amountFilter, setAmountFilter] = useState<AmountFilter>("all");
  const [termFilter, setTermFilter] = useState<TermFilter>("all");
  const [sort, setSort] = useState<Sort>("newest");
  const [page, setPage] = useState(1);
  const totalAmount = useMemo(() => data.opportunities.reduce((sum, item) => sum + item.amountCents, 0), [data.opportunities]);
  const supportsRisk = data.opportunities.some((item) => item.risk !== null);
  const sectors = useMemo(() => [...new Set(data.opportunities.map((item) => item.sector).filter((sector): sector is string => sector !== null))].sort(), [data.opportunities]);
  const filtered = useMemo(() => data.opportunities.filter((item) => matchesOpportunity(item, query, quickFilter, sectorFilter, amountFilter, termFilter)).sort((a, b) => sortOpportunities(a, b, sort)), [data.opportunities, query, quickFilter, sectorFilter, amountFilter, termFilter, sort]);
  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, pageCount);
  const visible = filtered.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE);
  const start = filtered.length ? (safePage - 1) * PAGE_SIZE + 1 : 0;
  const end = Math.min(safePage * PAGE_SIZE, filtered.length);
  const resetPage = <T,>(setter: (value: T) => void) => (value: T) => { setter(value); setPage(1); };

  return <div className="mx-auto max-w-[1380px]"><header className="flex flex-wrap items-start justify-between gap-4"><div><h1 className="text-[38px] font-bold leading-none tracking-[-.04em] text-navy">Marketplace</h1><p className="mt-1.5 text-[17px] text-[#1d54b7]">Encuentra facturas de empresas confiables y haz crecer tu capital.</p></div><article className="flex w-full items-center gap-4 rounded-xl bg-[#f0f4ff] px-5 py-3 sm:w-auto sm:min-w-[365px]"><span className="flex h-12 w-12 items-center justify-center rounded-xl bg-white text-[#175ee3]"><Icon name="wallet" size={25}/></span><div><p className="text-sm text-[#38517d]">Disponible para financiar</p><strong className="mt-1 block text-[25px] leading-none text-navy">{formatCents(data.availableCapitalCents)}</strong><p className="mt-1.5 text-xs text-[#1d54b7]">Fondos disponibles para nuevas oportunidades</p></div></article></header>
    <section className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4"><MarketplaceKpiCard label="Facturas disponibles" value={String(data.opportunities.length)} detail="Buscando financiamiento" icon="invoice" tone="blue"/><MarketplaceKpiCard label="Monto buscando financiamiento" value={`${formatCents(totalAmount)} MXN`} detail={`En ${data.opportunities.length} facturas`} icon="coins" tone="green"/><MarketplaceKpiCard label="Retorno promedio" value={data.averageReturnRate === null ? "—" : `${data.averageReturnRate}%`} detail="De las oportunidades disponibles" icon="percent" tone="green"/><MarketplaceKpiCard label="Deudores que ya conoces" value={data.knownDebtorsCount === null ? "—" : String(data.knownDebtorsCount)} detail="Oportunidades con deudores que has financiado antes" icon="shield" tone="green"/></section>
    <section className="mt-4 flex flex-wrap items-center gap-2.5"><label className="flex h-11 min-w-[330px] flex-1 items-center gap-3 rounded-xl bg-[#f1f5fa] px-4 text-[#52688f] xl:max-w-[480px]"><Icon name="search" size={20}/><input value={query} onChange={(event) => resetPage(setQuery)(event.target.value)} className="w-full bg-transparent text-sm text-navy outline-none placeholder:text-[#6b7fa5]" placeholder="Buscar deudor, empresa o factura..."/></label><QuickButton label="Todas" active={quickFilter === "all"} onClick={() => resetPage(setQuickFilter)("all")}/><QuickButton label="Deudores conocidos" active={quickFilter === "known"} disabled={data.knownDebtorsCount === null} onClick={() => resetPage(setQuickFilter)("known")}/><QuickButton label="Riesgo bajo" tone="green" active={quickFilter === "low"} disabled={!supportsRisk} onClick={() => resetPage(setQuickFilter)("low")}/><QuickButton label="Riesgo medio" tone="orange" active={quickFilter === "medium"} disabled={!supportsRisk} onClick={() => resetPage(setQuickFilter)("medium")}/><QuickButton label="Riesgo alto" tone="red" active={quickFilter === "high"} disabled={!supportsRisk} onClick={() => resetPage(setQuickFilter)("high")}/></section>
    <section className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-[1fr_1fr_1fr_1.1fr]"><FilterSelect label="Sector" value={sectorFilter} disabled={sectors.length === 0} onChange={(value) => resetPage(setSectorFilter)(value)} options={[{ value: "all", label: "Todos los sectores" }, ...sectors.map((sector) => ({ value: sector, label: sectorLabel(sector) }))]}/><FilterSelect label="Monto" value={amountFilter} onChange={(value) => resetPage(setAmountFilter)(value as AmountFilter)} options={[{ value: "all", label: "Cualquier monto" }, { value: "under_100", label: "Menos de $100 mil" }, { value: "100_500", label: "$100 mil a $500 mil" }, { value: "over_500", label: "Más de $500 mil" }]}/><FilterSelect label="Plazo" value={termFilter} onChange={(value) => resetPage(setTermFilter)(value as TermFilter)} options={[{ value: "all", label: "Cualquier plazo" }, { value: "under_30", label: "Menos de 30 días" }, { value: "30_60", label: "30 a 60 días" }, { value: "over_60", label: "Más de 60 días" }]}/><FilterSelect label="Ordenar por" value={sort} icon onChange={(value) => resetPage(setSort)(value as Sort)} options={[{ value: "newest", label: "Más recientes" }, { value: "amount_desc", label: "Mayor monto" }, { value: "amount_asc", label: "Menor monto" }]}/></section>
    <section className="mt-4 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-[0_8px_24px_rgba(15,31,68,.025)]">{visible.length ? <MarketplaceTable opportunities={visible}/> : <div className="px-6 py-16 text-center"><h2 className="text-lg font-semibold text-navy">No hay facturas disponibles en este momento.</h2><p className="mt-2 text-sm text-[#52688f]">Prueba cambiando los filtros o vuelve más tarde.</p></div>}<footer className="flex min-h-14 flex-wrap items-center justify-between gap-4 border-t border-slate-200 px-4 py-3 text-xs text-[#1d54b7]"><span>Mostrando {start}–{end} de {filtered.length} facturas</span><div className="flex items-center gap-1"><PageButton label="Anterior" disabled={safePage === 1} onClick={() => setPage((current) => Math.max(1, current - 1))}>‹</PageButton>{Array.from({ length: pageCount }, (_, index) => index + 1).map((number) => <PageButton key={number} label={`Página ${number}`} active={number === safePage} onClick={() => setPage(number)}>{number}</PageButton>)}<PageButton label="Siguiente" disabled={safePage === pageCount} onClick={() => setPage((current) => Math.min(pageCount, current + 1))}>›</PageButton></div></footer></section>
  </div>;
}

function matchesOpportunity(item: MarketplaceOpportunity, query: string, quick: QuickFilter, sector: string, amount: AmountFilter, term: TermFilter): boolean {
  const needle = query.trim().toLocaleLowerCase("es-MX");
  const matchesQuery = !needle || item.folio.toLocaleLowerCase("es-MX").includes(needle) || item.debtor.toLocaleLowerCase("es-MX").includes(needle) || item.applicant.toLocaleLowerCase("es-MX").includes(needle);
  const matchesQuick = quick === "all" || (quick === "known" ? item.previouslyFinanced === true : item.risk === quick);
  const matchesSector = sector === "all" || item.sector === sector;
  const matchesAmount = amount === "all" || (amount === "under_100" && item.amountCents < 10_000_000) || (amount === "100_500" && item.amountCents >= 10_000_000 && item.amountCents <= 50_000_000) || (amount === "over_500" && item.amountCents > 50_000_000);
  const matchesTerm = term === "all" || (term === "under_30" && item.daysUntilDue < 30) || (term === "30_60" && item.daysUntilDue >= 30 && item.daysUntilDue <= 60) || (term === "over_60" && item.daysUntilDue > 60);
  return matchesQuery && matchesQuick && matchesSector && matchesAmount && matchesTerm;
}

const SECTOR_LABELS: Record<string, string> = {
  retail_chain: "Comercio minorista",
  construction_supplies: "Materiales de construcción",
  construction: "Construcción",
  manufacturing: "Manufactura",
  pharma_retail: "Farmacéutico",
  logistics: "Logística y transporte",
  technology: "Tecnología",
  textile: "Textil",
  agriculture: "Agroindustria",
  hospitality: "Hotelería",
};

function sectorLabel(sector: string): string {
  return SECTOR_LABELS[sector] ?? sector;
}

function sortOpportunities(a: MarketplaceOpportunity, b: MarketplaceOpportunity, sort: Sort): number {
  if (sort === "amount_desc") return b.amountCents - a.amountCents;
  if (sort === "amount_asc") return a.amountCents - b.amountCents;
  return b.issueDate.localeCompare(a.issueDate) || b.id - a.id;
}

function QuickButton({ label, active, disabled, tone, onClick }: { label: string; active: boolean; disabled?: boolean; tone?: "green" | "orange" | "red"; onClick: () => void }) {
  const dot = tone && <i className={`h-3 w-3 rounded-full ${tone === "green" ? "bg-emerald-500" : tone === "orange" ? "bg-amber-500" : "bg-rose-500"}`}/>;
  return <button type="button" disabled={disabled} onClick={onClick} title={disabled ? "Información no disponible en el backend" : undefined} className={`flex h-11 items-center gap-2 rounded-full border px-5 text-sm transition disabled:cursor-not-allowed disabled:opacity-45 ${active ? "border-navy bg-navy text-white" : "border-slate-200 bg-white text-navy hover:border-slate-400"}`}>{dot}{label}</button>;
}

function FilterSelect({ label, value, options, disabled, icon, onChange }: { label: string; value: string; options: { value: string; label: string }[]; disabled?: boolean; icon?: boolean; onChange?: (value: string) => void }) {
  return <label className="relative flex h-12 items-center gap-3 rounded-lg border border-slate-200 bg-white px-4">{icon && <Icon name="transfer" size={18}/>}<span className="min-w-0 flex-1"><span className="block text-[10px] text-[#1d54b7]">{label}</span><select value={value} disabled={disabled} onChange={(event) => onChange?.(event.target.value)} className="w-full appearance-none bg-transparent pr-6 text-sm text-navy outline-none disabled:cursor-not-allowed disabled:opacity-60">{options.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select></span><Icon name="chevron" size={16}/></label>;
}

function PageButton({ children, label, active, disabled, onClick }: { children: React.ReactNode; label: string; active?: boolean; disabled?: boolean; onClick: () => void }) {
  return <button type="button" aria-label={label} disabled={disabled} onClick={onClick} className={`flex h-8 min-w-8 items-center justify-center rounded-lg px-2 disabled:opacity-30 ${active ? "bg-[#eef3fb] font-semibold text-navy" : "hover:bg-slate-50"}`}>{children}</button>;
}
