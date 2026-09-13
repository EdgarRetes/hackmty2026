"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { MarketplaceDetailData } from "@/lib/marketplace-detail";
import { Icon } from "../icons";
import { InvoiceSummary } from "../offers/invoice-summary";
import { PageBackLink } from "../page-back-link";

export function MarketplacePublicationDetail({ batchId, data }: { batchId: number; data: MarketplaceDetailData }) {
  const router = useRouter();
  const [advance, setAdvance] = useState(85);
  const [returnRate, setReturnRate] = useState(2.5);

  function submitCustomOffer() {
    router.push(`/marketplace/${batchId}/offer-success?advance=${encodeURIComponent(String(advance))}&return=${encodeURIComponent(String(returnRate))}`);
  }

  return <div className="mx-auto max-w-[1280px]">
    <header className="flex items-start gap-3"><PageBackLink href="/marketplace" label="Volver al Marketplace"/><div><h1 className="text-[38px] font-bold leading-none tracking-[-.045em] text-navy">{data.publication.id}</h1><p className="mt-1.5 text-[17px] text-[#1d54b7]">{data.isOpen ? "Define los términos de la oferta que quieres realizar." : "Esta publicación ya fue financiada."}</p></div></header>
    <InvoiceSummary invoice={data.publication}/>
    <section className="mt-4 rounded-xl border border-slate-200 bg-white px-5 py-4"><h2 className="text-sm font-semibold text-navy">Facturas incluidas ({data.invoices.length})</h2><ul className="mt-3 grid gap-2 sm:grid-cols-2 xl:grid-cols-3">{data.invoices.map((invoice) => <li key={invoice.id} className="flex items-center justify-between gap-3 rounded-lg bg-[#f6f8fb] px-3 py-2 text-sm"><span className="flex items-center gap-2 font-medium text-navy"><Icon name="invoice" size={16}/>#{invoice.folio}</span><span className="text-[#52688f]">{invoice.client}</span><span className="font-semibold text-navy">{invoice.amount}</span><button type="button" className="shrink-0 rounded-lg bg-[#eaf2ff] px-3 py-2 text-xs font-semibold text-[#075ad9]" title="El detalle de factura estará disponible próximamente">Ver factura</button></li>)}</ul></section>
    {data.isOpen && <section className="mt-4 rounded-xl border border-blue-200 bg-[#f7faff] p-5 shadow-[0_8px_24px_rgba(15,31,68,.025)]"><div><h2 className="text-lg font-bold text-navy">Haz tu oferta</h2><p className="mt-1 text-sm text-[#52688f]">Establece los términos que deseas proponer. No se muestran ofertas ni condiciones de otras financiadoras.</p></div><div className="mt-5 grid gap-4 sm:grid-cols-2"><label className="block"><span className="text-xs font-medium text-[#38517d]">Anticipo que deseas ofrecer</span><div className="mt-2 flex items-center rounded-lg border border-slate-200 bg-white px-3"><input type="number" min="50" max="100" step="0.1" value={advance} onChange={(event) => setAdvance(Number(event.target.value))} className="h-11 w-full bg-transparent text-sm font-semibold text-navy outline-none"/><span className="text-sm text-[#52688f]">%</span></div></label><label className="block"><span className="text-xs font-medium text-[#38517d]">Retorno que deseas ofrecer</span><div className="mt-2 flex items-center rounded-lg border border-slate-200 bg-white px-3"><input type="number" min="0.1" max="20" step="0.1" value={returnRate} onChange={(event) => setReturnRate(Number(event.target.value))} className="h-11 w-full bg-transparent text-sm font-semibold text-navy outline-none"/><span className="text-sm text-[#52688f]">%</span></div></label></div><p className="mt-3 text-xs text-[#52688f]">Estos términos se preparan en esta prueba local; no se envían ni modifican datos del backend.</p><button type="button" onClick={submitCustomOffer} className="mt-5 h-11 rounded-xl bg-navy px-5 text-sm font-semibold text-white transition hover:bg-[#17315f]">Enviar oferta personalizada</button></section>}
  </div>;
}
