"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import type { InvoiceListItem, InvoiceUiStatus } from "@/lib/invoices";
import { createPublication } from "@/lib/publications";
import { Icon } from "../icons";
import { InvoiceSummaryCard } from "./invoice-summary-card";
import { InvoiceTable } from "./invoice-table";

const PAGE_SIZE = 8;
const filters: { label: string; value: "all" | InvoiceUiStatus }[] = [
  { label: "Todas", value: "all" }, { label: "No aplica", value: "not_applicable" },
  { label: "Publicadas", value: "published" }, { label: "Financiadas", value: "funded" },
];

export function InvoicesPageContent({ invoices }: { invoices: InvoiceListItem[] }) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<"all" | InvoiceUiStatus>("all");
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<number[]>([]);
  const [publishing, setPublishing] = useState(false);
  const [publishError, setPublishError] = useState<string | null>(null);
  function toggleSelected(id: number) {
    setSelected((current) => (current.includes(id) ? current.filter((value) => value !== id) : [...current, id]));
  }
  async function handlePublish() {
    setPublishing(true);
    setPublishError(null);
    try {
      const batch = await createPublication(selected);
      router.push(`/publications/${batch.id}`);
    } catch (error) {
      setPublishError(error instanceof Error ? error.message : "No se pudo publicar el paquete.");
      setPublishing(false);
    }
  }
  const summaries = useMemo(() => [
    summarize("Total de facturas", invoices),
    summarize("No aplica", invoices.filter((invoice) => invoice.status === "not_applicable")),
    summarize("Publicadas", invoices.filter((invoice) => invoice.status === "published")),
    summarize("Financiadas", invoices.filter((invoice) => invoice.status === "funded")),
  ], [invoices]);
  const filtered = useMemo(() => invoices.filter((invoice) => {
    const matchesStatus = status === "all" || invoice.status === status;
    const needle = query.trim().toLocaleLowerCase("es-MX");
    return matchesStatus && (!needle || invoice.folio.toLocaleLowerCase("es-MX").includes(needle) || invoice.client.toLocaleLowerCase("es-MX").includes(needle));
  }).sort((a, b) => b.issueDate.localeCompare(a.issueDate)), [invoices, query, status]);
  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, pageCount);
  const visible = filtered.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE);
  const start = filtered.length ? (safePage - 1) * PAGE_SIZE + 1 : 0;
  const end = Math.min(safePage * PAGE_SIZE, filtered.length);
  function updateQuery(value: string) { setQuery(value); setPage(1); }
  function updateStatus(value: "all" | InvoiceUiStatus) { setStatus(value); setPage(1); }

  return <div className="mx-auto max-w-[1380px]"><div className="flex items-start justify-between gap-4"><div><h1 className="text-[38px] font-bold leading-none tracking-[-.04em] text-navy">Facturas</h1><p className="mt-1.5 text-[17px] text-[#52688f]">Consulta y administra las facturas de tu empresa.</p></div><button onClick={() => router.push("/invoices/package")} className="rounded-xl bg-navy px-5 py-3 text-sm font-semibold text-white">Crear paquete</button></div>
    <section className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4"><InvoiceSummaryCard {...summaries[0]} tone="navy" icon="invoice"/><InvoiceSummaryCard {...summaries[1]} tone="gray" icon="clock"/><InvoiceSummaryCard {...summaries[2]} tone="purple" icon="bars"/><InvoiceSummaryCard {...summaries[3]} tone="green" icon="check"/></section>
    <section className="mt-5 flex flex-wrap items-center gap-2.5"><label className="flex h-11 min-w-[300px] flex-1 items-center gap-3 rounded-xl border border-slate-200 bg-[#f6f8fb] px-4 text-[#52688f] xl:max-w-[435px]"><Icon name="search" size={20}/><input value={query} onChange={(event) => updateQuery(event.target.value)} className="w-full bg-transparent text-sm text-navy outline-none placeholder:text-[#6b7fa5]" placeholder="Buscar por factura o cliente..."/></label>{filters.map((filter) => <button key={filter.value} onClick={() => updateStatus(filter.value)} className={`h-11 rounded-full border px-6 text-sm transition ${status === filter.value ? "border-navy bg-navy text-white shadow-sm" : "border-slate-200 bg-white text-[#38517d] hover:border-slate-400"}`}>{filter.label}</button>)}<button className="ml-auto flex h-11 items-center gap-3 rounded-xl border border-slate-200 bg-white px-5 text-sm font-medium text-navy"><Icon name="transfer" size={18}/>Más recientes <Icon name="chevron" size={16}/></button></section>
    {selected.length > 0 && <section className="mt-4 flex flex-wrap items-center gap-3 rounded-xl border border-[#d1baff] bg-[#f5efff] px-4 py-3"><span className="text-sm font-semibold text-navy">{selected.length} factura{selected.length === 1 ? "" : "s"} seleccionada{selected.length === 1 ? "" : "s"}</span><span className="text-xs text-[#52688f]">{selected.length === 1 ? "Se publicará como una oportunidad individual en el marketplace." : "Se publicarán juntas: una financiadora puede pagar todas y quedarse con el rendimiento del conjunto."}</span><button onClick={handlePublish} disabled={publishing} className="ml-auto flex h-10 items-center gap-2 rounded-lg bg-[#6330e8] px-5 text-sm font-semibold text-white transition hover:bg-[#5827c9] disabled:cursor-not-allowed disabled:opacity-50">{publishing ? "Publicando..." : "Publicar"}</button><button onClick={() => setSelected([])} className="text-xs font-medium text-[#52688f] hover:text-navy">Limpiar selección</button></section>}
    {publishError && <p role="alert" className="mt-3 rounded-lg border border-red-200 bg-red-50 px-4 py-2.5 text-sm text-red-700">{publishError}</p>}
    <section className="mt-5 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-[0_8px_24px_rgba(15,31,68,.025)]">{visible.length ? <InvoiceTable invoices={visible} selectable selectedIds={selected} onToggle={toggleSelected}/> : <div className="px-6 py-16 text-center"><h2 className="text-lg font-semibold text-navy">No encontramos facturas disponibles.</h2><p className="mt-2 text-sm text-[#52688f]">Prueba cambiando la búsqueda o el filtro seleccionado.</p></div>}<footer className="flex min-h-16 flex-wrap items-center justify-between gap-4 border-t border-slate-200 px-5 py-3 text-xs text-[#52688f]"><span>Mostrando {start}–{end} de {filtered.length} facturas</span><div className="flex items-center gap-1"><PageButton label="Anterior" disabled={safePage === 1} onClick={() => setPage((current) => Math.max(1, current - 1))}>‹</PageButton>{Array.from({ length: pageCount }, (_, index) => index + 1).map((number) => <PageButton key={number} label={`Página ${number}`} active={number === safePage} onClick={() => setPage(number)}>{number}</PageButton>)}<PageButton label="Siguiente" disabled={safePage === pageCount} onClick={() => setPage((current) => Math.min(pageCount, current + 1))}>›</PageButton></div></footer></section>
  </div>;
}

function summarize(label: string, invoices: InvoiceListItem[]) { return { label, count: invoices.length, amount: `${new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN", maximumFractionDigits: 2 }).format(invoices.reduce((sum, invoice) => sum + invoice.amount, 0))} MXN` }; }
function PageButton({ children, label, active, disabled, onClick }: { children: React.ReactNode; label: string; active?: boolean; disabled?: boolean; onClick: () => void }) { return <button aria-label={label} disabled={disabled} onClick={onClick} className={`flex h-8 min-w-8 items-center justify-center rounded-lg px-2 transition disabled:opacity-30 ${active ? "bg-slate-100 font-semibold text-navy" : "hover:bg-slate-50"}`}>{children}</button>; }
