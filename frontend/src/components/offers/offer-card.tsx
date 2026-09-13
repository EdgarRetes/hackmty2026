"use client";

import { Icon } from "../icons";
import type { Offer, OfferTone } from "./data";

const tones: Record<OfferTone, { border: string; badge: string; text: string; button: string; panel: string }> = {
  lime: { border: "border-[#b9e52d]", badge: "bg-[#d6f36b]", text: "text-navy", button: "bg-[#d6f36b] hover:bg-[#c8e958]", panel: "bg-[#f1faea]" },
  blue: { border: "border-[#8dc6ff]", badge: "bg-[#e8f2ff]", text: "text-[#0663e5]", button: "bg-[#e8f2ff] hover:bg-[#d8eaff]", panel: "bg-[#edf6ff]" },
  purple: { border: "border-[#d1baff]", badge: "bg-[#f3eaff]", text: "text-[#6330e8]", button: "bg-[#f3eaff] hover:bg-[#e9dcff]", panel: "bg-[#f5efff]" },
  orange: { border: "border-[#ffc98f]", badge: "bg-[#ffebd9]", text: "text-[#c74d08]", button: "bg-[#ffebd9] hover:bg-[#ffe0c3]", panel: "bg-[#fff2e5]" },
};

export function OfferCard({ offer, onAccept, accepting }: { offer: Offer; onAccept?: (offerId: string) => void; accepting?: boolean }) {
  const tone = tones[offer.tone];
  return <article className={`flex min-w-0 flex-col rounded-xl border bg-white p-3.5 shadow-[0_8px_24px_rgba(15,31,68,.025)] transition hover:-translate-y-1 hover:shadow-lg ${tone.border}`}>
    <div className="flex min-h-10 items-center justify-between gap-2"><div className="flex min-w-0 items-center gap-2"><span className={`text-lg font-black ${tone.text}`}>{offer.mark}</span><span className="truncate text-[13px] font-bold text-navy">{offer.financier}</span></div><span className={`flex shrink-0 items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-[11px] font-medium ${tone.badge} ${tone.text}`}>{offer.tone === "lime" && <Icon name="star" size={13} className="fill-current"/>}{offer.category}</span></div>
    <p className="mt-3 text-xs text-[#52688f]">Recibirás</p><p className="mt-1 whitespace-nowrap text-[27px] font-bold leading-none tracking-[-.045em] text-navy">{offer.amount}</p>
    <div className="mt-3 grid grid-cols-2 border-t border-slate-200 pt-2.5"><div><p className="text-[11px] text-[#52688f]">Anticipo</p><strong className="mt-0.5 block text-lg text-navy">{offer.advance}</strong></div><div><p className="text-[11px] text-[#52688f]">Comisión</p><strong className="mt-0.5 block text-lg text-navy">{offer.commission}</strong></div></div>
    <div className="mt-3.5 grid grid-cols-2 gap-2"><div className="flex gap-1.5"><Icon name="coins" size={24} className={tone.text}/><div><p className="text-[9px] leading-3 text-[#52688f]">Costo de financiamiento</p><strong className="mt-0.5 block whitespace-nowrap text-[11px] text-navy">{offer.cost}</strong></div></div><div className="flex gap-1.5"><Icon name={offer.tone === "purple" ? "clock" : "bolt"} size={24} className={tone.text}/><div><p className="text-[9px] leading-3 text-[#52688f]">Desembolso</p><strong className="mt-0.5 block whitespace-nowrap text-[11px] text-navy">{offer.funding}</strong></div></div></div>
    <button onClick={() => offer.action === "Aceptar oferta" && onAccept?.(offer.id)} disabled={accepting} className={`mt-4 h-10 rounded-lg text-sm font-semibold transition active:scale-[.98] disabled:cursor-wait disabled:opacity-60 ${tone.button} ${offer.tone === "lime" ? "text-navy" : tone.text}`}>{accepting ? "Aceptando..." : offer.action}</button>
    <div className={`mt-2 flex min-h-[56px] items-center gap-2.5 rounded-lg px-2.5 py-2 ${tone.panel}`}><Icon name={offer.tone === "purple" ? "bars" : offer.tone === "lime" ? "check" : offer.tone === "blue" ? "star" : "bolt"} size={23} className={`shrink-0 ${tone.text}`}/><p className="text-[11px] leading-[1.4] text-[#38517d]">{offer.explanation}</p></div>
  </article>;
}
