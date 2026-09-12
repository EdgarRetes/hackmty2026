import { Icon } from "../icons";
import type { InvoiceDetails } from "./data";

export function InvoiceSummary({ invoice }: { invoice: InvoiceDetails }) {
  const shownId = invoice.id.startsWith("#") ? invoice.id : `#${invoice.id}`;
  const isVerified = invoice.status === "Verificada" || invoice.status === "Financiada" || invoice.status === "Pagada";
  return <section className="mt-4 grid rounded-xl border border-slate-200 bg-white px-5 py-4 shadow-[0_8px_30px_rgba(15,31,68,.03)] md:grid-cols-[1.15fr_1fr_1fr]">
    <div className="flex gap-4 border-b border-slate-200 pb-4 md:border-b-0 md:border-r md:pb-0 md:pr-6"><div className="flex h-[66px] w-[66px] shrink-0 items-center justify-center rounded-xl bg-[#f3eaff] text-navy"><Icon name="invoice" size={32}/></div><div><p className="text-xs text-[#52688f]">Factura</p><div className="mt-1 flex flex-wrap items-center gap-2.5"><strong className="text-[22px] tracking-[-.04em] text-navy">{shownId}</strong><span className={`flex items-center gap-1.5 rounded-xl px-2.5 py-1 text-xs font-semibold ${isVerified ? "bg-[#daf7e6] text-[#079455]" : "bg-slate-100 text-[#52688f]"}`}><span className={`flex h-4 w-4 items-center justify-center rounded-full ${isVerified ? "bg-[#0aa45c] text-white" : "bg-slate-300 text-white"}`}><Icon name="check" size={12}/></span>{invoice.status}</span></div><p className="mt-1 text-[11px] text-[#52688f]">Cliente</p><p className="text-sm font-semibold text-navy">{invoice.client}</p></div></div>
    <div className="border-b border-slate-200 py-4 md:border-b-0 md:border-r md:px-7 md:py-0"><p className="text-xs text-[#52688f]">Monto de la factura</p><strong className="mt-2 block text-[23px] tracking-[-.04em] text-navy">{invoice.amount}</strong></div>
    <div className="pt-4 md:pl-7 md:pt-0"><p className="text-xs text-[#52688f]">Fecha de vencimiento</p><div className="mt-2 flex items-start gap-3"><Icon name="calendar" size={24}/><div><strong className="block text-lg text-navy">{invoice.dueDate}</strong><span className="mt-0.5 block text-xs text-[#52688f]">(en {invoice.daysRemaining} días)</span></div></div></div>
  </section>;
}
