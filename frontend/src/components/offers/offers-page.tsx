"use client";

import { useMemo, useState } from "react";
import { acceptOffer } from "@/lib/offers";
import { Icon } from "../icons";
import type { OffersPageData } from "./data";
import { InvoiceSummary } from "./invoice-summary";
import { OfferCard } from "./offer-card";
import { RiskAssessmentCard } from "./risk-assessment-card";

const filters = ["Mejor oferta para ti", "Menor comisión", "Mayor anticipo", "Más rápido"] as const;

export function OffersPageContent({ data }: { data: OffersPageData }) {
  const [active, setActive] = useState<(typeof filters)[number]>(filters[0]);
  const [acceptingId, setAcceptingId] = useState<string | null>(null);
  const [acceptanceMessage, setAcceptanceMessage] = useState<string | null>(null);
  const sorted = useMemo(() => {
    if (active === "Menor comisión") return [...data.offers].sort((a, b) => a.commissionValue - b.commissionValue);
    if (active === "Mayor anticipo") return [...data.offers].sort((a, b) => b.advanceValue - a.advanceValue);
    return [...data.offers].sort((a, b) => a.rank - b.rank);
  }, [active, data.offers]);
  async function handleAccept(offerId: string) {
    setAcceptingId(offerId);
    setAcceptanceMessage(null);
    try {
      const result = await acceptOffer(offerId);
      setAcceptanceMessage(`Oferta aceptada. Transacción ${result.transaction_id}`);
    } catch (error) {
      setAcceptanceMessage(error instanceof Error ? error.message : "No se pudo aceptar la oferta.");
    } finally {
      setAcceptingId(null);
    }
  }
  return <div className="mx-auto max-w-[1280px]">
    <h1 className="text-[38px] font-bold leading-none tracking-[-.045em] text-navy">Ofertas</h1><p className="mt-1.5 text-[17px] text-[#52688f]">Compara las mejores opciones de financiamiento para tu factura.</p>
    <InvoiceSummary invoice={data.invoice}/>
    <RiskAssessmentCard assessment={data.riskAssessment}/>
    <div className="mt-4 flex flex-wrap items-center gap-2"><span className="mr-2 flex items-center gap-3 text-sm font-semibold text-navy">Ordenar por <Icon name="chevron" size={16}/></span>{filters.map((filter) => <button key={filter} onClick={() => setActive(filter)} aria-pressed={active === filter} className={`h-9 rounded-full border px-5 text-[13px] transition active:scale-[.98] ${active === filter ? "border-navy bg-navy text-white shadow-md" : "border-slate-200 bg-white text-navy hover:border-slate-400"}`}>{filter}</button>)}<button className="ml-auto flex h-9 items-center gap-2.5 rounded-lg border border-slate-200 bg-white px-4 text-[13px] text-navy transition hover:bg-slate-50"><Icon name="compare" size={17}/>Comparar ofertas (0)</button></div>
    {acceptanceMessage && <p role="status" className="mt-4 rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-navy">{acceptanceMessage}</p>}
    {sorted.length > 0 ? <section className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{sorted.map((offer) => <OfferCard key={offer.id} offer={offer} onAccept={handleAccept} accepting={acceptingId === offer.id}/>)}</section> : <OffersEmptyState decision={data.riskAssessment.decision}/>}
    <section className="mt-5 flex flex-col gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3.5 shadow-[0_8px_30px_rgba(15,31,68,.025)] sm:flex-row sm:items-center"><div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[#fff2e5] text-orange-500"><Icon name="bars" size={25}/></div><div><h2 className="text-base font-bold text-navy">¿Cómo elegimos estas ofertas?</h2><p className="mt-0.5 text-[13px] text-[#52688f]">Nuestro algoritmo analiza el monto de tu factura, el tiempo de vencimiento y las condiciones de cada financiadora para mostrarte las mejores opciones.</p></div><button className="flex h-9 shrink-0 items-center justify-center gap-2 rounded-lg border border-blue-200 px-4 text-[13px] font-medium text-blue-600 transition hover:bg-blue-50 sm:ml-auto">Conocer más <Icon name="arrow" size={15}/></button></section>
  </div>;
}

function OffersEmptyState({ decision }: { decision: "APPROVE" | "REVIEW" | "REJECT" }) {
  const copy = decision === "REVIEW"
    ? ["La factura requiere revisión manual.", "Completa o valida la información señalada antes de solicitar ofertas."]
    : decision === "REJECT"
      ? ["La factura no es elegible para ofertas automáticas.", "Consulta los motivos de la evaluación y corrige los datos que sea posible subsanar."]
      : ["Aún no hay ofertas disponibles para esta factura.", "Las nuevas propuestas de financiamiento aparecerán aquí."];
  return <section className="mt-4 rounded-xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center"><h2 className="text-lg font-semibold text-navy">{copy[0]}</h2><p className="mt-2 text-sm text-[#52688f]">{copy[1]}</p></section>;
}
