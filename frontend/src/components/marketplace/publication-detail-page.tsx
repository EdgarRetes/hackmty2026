"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { acceptPublication, type MarketplaceDetailData } from "@/lib/marketplace-detail";
import { Icon } from "../icons";
import { InvoiceSummary } from "../offers/invoice-summary";
import { OfferCard } from "../offers/offer-card";

export function MarketplacePublicationDetail({ batchId, data }: { batchId: number; data: MarketplaceDetailData }) {
  const router = useRouter();
  const [acceptingId, setAcceptingId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const sorted = [...data.offers].sort((a, b) => a.rank - b.rank);

  async function handleAccept(offerId: string) {
    const offer = data.offers.find((item) => item.id === offerId);
    if (!offer) return;
    setAcceptingId(offerId);
    setMessage(null);
    try {
      const result = await acceptPublication(batchId, offer.lenderId);
      setMessage(`Publicación financiada. Transacción ${result.transaction_id}.`);
      router.refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "No se pudo hacer la oferta.");
    } finally {
      setAcceptingId(null);
    }
  }

  return <div className="mx-auto max-w-[1280px]">
    <h1 className="text-[38px] font-bold leading-none tracking-[-.045em] text-navy">{data.publication.id}</h1>
    <p className="mt-1.5 text-[17px] text-[#1d54b7]">{data.isOpen ? "Elige la estrategia con la que quieres financiar esta publicación." : "Esta publicación ya fue financiada."}</p>
    <InvoiceSummary invoice={data.publication}/>
    <section className="mt-4 rounded-xl border border-slate-200 bg-white px-5 py-4"><h2 className="text-sm font-semibold text-navy">Facturas incluidas ({data.invoices.length})</h2><ul className="mt-3 grid gap-2 sm:grid-cols-2 xl:grid-cols-3">{data.invoices.map((invoice) => <li key={invoice.id} className="flex items-center justify-between gap-3 rounded-lg bg-[#f6f8fb] px-3 py-2 text-sm"><span className="flex items-center gap-2 font-medium text-navy"><Icon name="invoice" size={16}/>#{invoice.folio}</span><span className="text-[#52688f]">{invoice.client}</span><span className="font-semibold text-navy">{invoice.amount}</span></li>)}</ul></section>
    {message && <p role="status" className="mt-4 rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-navy">{message}</p>}
    {sorted.length > 0 ? <section className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{sorted.map((offer) => <OfferCard key={offer.id} offer={offer} onAccept={data.isOpen ? handleAccept : undefined} accepting={acceptingId === offer.id}/>)}</section> : <p className="mt-4 rounded-xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center text-sm text-[#52688f]">No hay estrategias de precio disponibles para esta publicación.</p>}
  </div>;
}
