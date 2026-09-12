"use client";

import { useMemo, useState } from "react";
import type { PublicationPageData } from "@/lib/publications";
import { Icon } from "../icons";
import { InvoiceSummary } from "../offers/invoice-summary";
import { OfferCard } from "../offers/offer-card";

const filters = ["Mejor oferta para ti", "Menor comisión", "Mayor anticipo", "Más rápido"] as const;

export function PublicationPageContent({ data }: { data: PublicationPageData }) {
  const [active, setActive] = useState<(typeof filters)[number]>(filters[0]);
  const sorted = useMemo(() => {
    if (active === "Menor comisión") return [...data.offers].sort((a, b) => a.commissionValue - b.commissionValue);
    if (active === "Mayor anticipo") return [...data.offers].sort((a, b) => b.advanceValue - a.advanceValue);
    return [...data.offers].sort((a, b) => a.rank - b.rank);
  }, [active, data.offers]);

  // No accept action here on purpose: batch offers are computed on the
  // fly with a synthetic id, not a real persisted Offer — see
  // API_CONTRACT.md. Accepting a whole package isn't implemented yet.

  return <div className="mx-auto max-w-[1280px]">
    <h1 className="text-[38px] font-bold leading-none tracking-[-.045em] text-navy">{data.publication.id}</h1>
    <p className="mt-1.5 text-[17px] text-[#52688f]">Compara las mejores opciones de financiamiento para este paquete de facturas.</p>
    <InvoiceSummary invoice={data.publication}/>
    <section className="mt-4 rounded-xl border border-slate-200 bg-white px-5 py-4"><h2 className="text-sm font-semibold text-navy">Facturas incluidas en este paquete ({data.invoices.length})</h2><ul className="mt-3 grid gap-2 sm:grid-cols-2 xl:grid-cols-3">{data.invoices.map((invoice) => <li key={invoice.id} className="flex items-center justify-between gap-3 rounded-lg bg-[#f6f8fb] px-3 py-2 text-sm"><span className="flex items-center gap-2 font-medium text-navy"><Icon name="invoice" size={16}/>#{invoice.folio}</span><span className="text-[#52688f]">{invoice.client}</span><span className="font-semibold text-navy">{invoice.amount}</span></li>)}</ul></section>
    <div className="mt-4 flex flex-wrap items-center gap-2"><span className="mr-2 flex items-center gap-3 text-sm font-semibold text-navy">Ordenar por <Icon name="chevron" size={16}/></span>{filters.map((filter) => <button key={filter} onClick={() => setActive(filter)} aria-pressed={active === filter} className={`h-9 rounded-full border px-5 text-[13px] transition active:scale-[.98] ${active === filter ? "border-navy bg-navy text-white shadow-md" : "border-slate-200 bg-white text-navy hover:border-slate-400"}`}>{filter}</button>)}</div>
    {sorted.length > 0 ? <section className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{sorted.map((offer) => <OfferCard key={offer.id} offer={offer}/>)}</section> : <PublicationEmptyState/>}
    <section className="mt-5 flex flex-col gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3.5 shadow-[0_8px_30px_rgba(15,31,68,.025)] sm:flex-row sm:items-center"><div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[#f3eaff] text-[#7c3aed]"><Icon name="bars" size={25}/></div><div><h2 className="text-base font-bold text-navy">¿Cómo se calculan estas ofertas?</h2><p className="mt-0.5 text-[13px] text-[#52688f]">Cada financiadora evalúa el riesgo y el monto de cada factura del paquete por separado y combina el resultado en una sola oferta: el anticipo y la tasa mostrados son el promedio ponderado por monto de las {data.invoices.length} facturas.</p></div></section>
  </div>;
}

function PublicationEmptyState() {
  return <section className="mt-4 rounded-xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center"><h2 className="text-lg font-semibold text-navy">Aún no hay ofertas disponibles para este paquete.</h2><p className="mt-2 text-sm text-[#52688f]">Las nuevas propuestas de financiamiento aparecerán aquí.</p></section>;
}
