"use client";

import { useMemo, useState } from "react";
import { formatCents } from "@/lib/marketplace";
import type { PortfolioData, PortfolioOperation, PortfolioStatus } from "@/lib/portfolio";
import { DashboardKpi } from "../financier-dashboard/dashboard-kpi";
import { Icon } from "../icons";

const PAGE_SIZE = 8;
type Filter = "all" | PortfolioStatus;

export function PortfolioPageContent({ data }: { data: PortfolioData }) {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<Filter>("all");
  const [page, setPage] = useState(1);
  const filtered = useMemo(() => data.operations.filter((operation) => {
    const needle = query.trim().toLocaleLowerCase("es-MX");
    return (!needle || operation.invoiceFolio.toLocaleLowerCase("es-MX").includes(needle) || operation.debtor.toLocaleLowerCase("es-MX").includes(needle)) && (filter === "all" || operation.status === filter);
  }), [data.operations, filter, query]);
  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, pageCount);
  const visible = filtered.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE);
  const counts = { all: data.operations.length, active: data.operations.filter((item) => item.status === "active").length, completed: data.operations.filter((item) => item.status === "completed").length };
  function applyFilter(next: Filter) { setFilter(next); setPage(1); }

  return <div className="mx-auto max-w-[1380px]"><header><h1 className="text-[38px] font-bold leading-none tracking-[-.04em] text-navy">Portafolio</h1><p className="mt-2 text-[17px] text-[#1d54b7]">Consulta el capital que tienes colocado y el estado de tus financiamientos.</p></header><section className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4"><DashboardKpi label="Capital financiado" value={`${formatCents(data.financedCapitalCents)} MXN`} detail="Total de capital colocado" icon="coins" tone="orange"/><DashboardKpi label="Operaciones activas" value={String(data.activeOperationsCount)} detail="Financiamientos en curso" icon="bars" tone="teal"/><DashboardKpi label="Retorno esperado" value="—" detail="El backend no expone este agregado" icon="percent" tone="violet"/><DashboardKpi label="Capital recuperado" value="—" detail="Información no disponible" icon="wallet" tone="blue"/></section><section className="mt-4 overflow-hidden rounded-xl border border-slate-200 bg-white p-5 shadow-[0_8px_24px_rgba(15,31,68,.025)]"><div className="flex flex-wrap items-start justify-between gap-4"><div><h2 className="text-xl font-bold text-navy">Tus financiamientos</h2><p className="mt-1 text-sm text-[#52688f]">Lista de facturas que has financiado.</p></div><div className="flex flex-wrap gap-3"><label className="flex h-11 min-w-[290px] items-center gap-3 rounded-xl bg-[#f1f5fa] px-4 text-[#52688f]"><Icon name="search" size={19}/><input value={query} onChange={(event) => { setQuery(event.target.value); setPage(1); }} placeholder="Buscar factura o deudor..." className="w-full bg-transparent text-sm text-navy outline-none placeholder:text-[#6b7fa5]"/></label><span className="flex h-11 items-center gap-3 rounded-xl border border-slate-200 px-4 text-sm font-medium text-navy">Más recientes <Icon name="chevron" size={16}/></span></div></div><div className="mt-4 flex flex-wrap gap-2">{([['all', 'Todos'], ['active', 'Activos'], ['completed', 'Completados']] as const).map(([value, label]) => <button key={value} type="button" onClick={() => applyFilter(value)} className={`rounded-full px-5 py-2 text-sm font-medium ${filter === value ? "bg-[#1764ed] text-white" : "bg-[#f0f4fa] text-[#38517d]"}`}>{label} ({counts[value]})</button>)}</div><div className="mt-4">{visible.length ? <PortfolioTable operations={visible}/> : <div className="py-14 text-center text-sm text-[#6b7fa5]">No hay financiamientos que coincidan con la búsqueda.</div>}</div><footer className="flex min-h-12 flex-wrap items-center justify-between gap-3 border-t border-slate-200 pt-4 text-xs text-[#1d54b7]"><span>Mostrando {filtered.length ? (safePage-1)*PAGE_SIZE+1 : 0}–{Math.min(safePage*PAGE_SIZE, filtered.length)} de {filtered.length} resultados</span><div className="flex gap-1">{Array.from({ length: pageCount }, (_, index) => index + 1).map((number) => <button key={number} type="button" onClick={() => setPage(number)} className={`h-8 min-w-8 rounded-lg ${number === safePage ? "bg-[#e8f1ff] font-semibold text-[#1764ed]" : "text-navy"}`}>{number}</button>)}</div></footer></section></div>;
}

function PortfolioTable({ operations }: { operations: PortfolioOperation[] }) {
  return <div className="overflow-x-auto"><table className="w-full min-w-[1020px] border-collapse text-left"><thead className="bg-[#f1f5fa] text-xs font-medium text-[#38517d]"><tr><th className="px-3 py-3">Factura</th><th className="px-3 py-3">Deudor</th><th className="px-3 py-3">Capital financiado</th><th className="px-3 py-3">Retorno esperado</th><th className="px-3 py-3">Fecha de financiamiento</th><th className="px-3 py-3">Estado</th><th className="px-3 py-3">Acción</th></tr></thead><tbody>{operations.map((operation) => <tr key={operation.id} className="border-t border-slate-200 text-[13px] text-navy hover:bg-slate-50/70"><td className="px-3 py-3 font-semibold">{operation.invoiceFolio}</td><td className="px-3 py-3">{operation.debtor}</td><td className="px-3 py-3 font-semibold">{operation.formattedFinancedCapital} MXN</td><td className="px-3 py-3">{operation.formattedExpectedReturn} MXN</td><td className="px-3 py-3 text-[#38517d]">{operation.formattedFinancedAt}</td><td className="px-3 py-3"><StatusBadge status={operation.status}/></td><td className="px-3 py-3"><span className="inline-flex min-w-[110px] justify-center rounded-lg bg-[#f1f6ff] px-4 py-2 text-xs font-semibold text-[#075ad9]" title="La ruta de detalle aún no está disponible">Ver detalles</span></td></tr>)}</tbody></table></div>;
}

function StatusBadge({ status }: { status: PortfolioStatus }) {
  return <span className={`inline-flex min-w-[96px] items-center justify-center gap-2 rounded-lg px-3 py-1.5 text-xs ${status === "active" ? "bg-emerald-50 text-emerald-700" : "bg-blue-50 text-blue-700"}`}><i className={`h-2 w-2 rounded-full ${status === "active" ? "bg-emerald-500" : "bg-blue-400"}`}/>{status === "active" ? "Activo" : "Completado"}</span>;
}
