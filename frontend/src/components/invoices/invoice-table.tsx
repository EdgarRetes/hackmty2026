import type { InvoiceListItem } from "@/lib/invoices";
import { Icon } from "../icons";
import { InvoiceStatusBadge } from "./invoice-status-badge";

export function InvoiceTable({
  invoices,
  selectable = false,
  selectedIds = [],
  onToggle,
}: {
  invoices: InvoiceListItem[];
  selectable?: boolean;
  selectedIds?: number[];
  onToggle?: (id: number) => void;
}) {
  return <div className="overflow-x-auto"><table className="w-full min-w-[960px] border-collapse text-left"><thead className="bg-[#f3f6fa] text-xs font-medium text-[#52688f]"><tr>{selectable && <th className="w-10 px-4 py-3"/>}<th className="px-5 py-3">Factura</th><th className="px-4 py-3">Cliente</th><th className="px-4 py-3">Monto</th><th className="px-4 py-3">Fecha de emisión</th><th className="px-4 py-3">Estado</th><th className="px-4 py-3 text-center">Ofertas</th><th className="px-4 py-3">Acciones</th><th className="w-10 py-3"/></tr></thead><tbody>{invoices.map((invoice) => {
    const canSelect = selectable && invoice.status === "not_applicable";
    return <tr key={invoice.id} className="border-t border-slate-200 text-[13px] text-navy transition hover:bg-slate-50/70">
      {selectable && <td className="px-4 py-3">{canSelect && <input type="checkbox" checked={selectedIds.includes(invoice.id)} onChange={() => onToggle?.(invoice.id)} className="h-4 w-4 rounded border-slate-300 accent-navy" aria-label={`Seleccionar ${invoice.folio}`}/>}</td>}
      <td className="px-5 py-3"><span className="flex items-center gap-3 font-semibold"><Icon name="invoice" size={18}/><span>#{invoice.folio}</span></span></td>
      <td className="px-4 py-3">{invoice.client}</td>
      <td className="px-4 py-3 font-semibold">{invoice.formattedAmount}</td>
      <td className="px-4 py-3">{invoice.formattedIssueDate}</td>
      <td className="px-4 py-3"><InvoiceStatusBadge status={invoice.status}/></td>
      <td className="px-4 py-3 text-center font-semibold">{invoice.offersCount || "-"}</td>
      <td className="px-4 py-3"><InvoiceAction invoice={invoice}/></td>
      <td className="pr-4 text-right"><button className="rounded-lg p-2 text-[#52688f] hover:bg-slate-100" aria-label={`Más opciones para ${invoice.folio}`}><span className="text-lg leading-none">⋮</span></button></td>
    </tr>;
  })}</tbody></table></div>;
}

function InvoiceAction({ invoice }: { invoice: InvoiceListItem }) {
  if (invoice.batchId) return <a href={`/publications/${invoice.batchId}`} className="inline-flex min-w-[116px] justify-center rounded-lg bg-[#f3eaff] px-4 py-2 text-xs font-medium text-[#7c3aed] transition hover:bg-[#ecdcff]">Ver publicación</a>;
  if (invoice.status === "published" && invoice.offersCount > 0) return <a href={`/offers/${encodeURIComponent(invoice.folio)}`} className="inline-flex min-w-[116px] justify-center rounded-lg bg-[#e6f3ff] px-4 py-2 text-xs font-medium text-[#0875d1] transition hover:bg-[#d8ebff]">Ver ofertas</a>;
  if (invoice.status === "funded") return <button className="min-w-[116px] rounded-lg bg-[#e6f3ff] px-4 py-2 text-xs font-medium text-[#0875d1] transition hover:bg-[#d8ebff]">Ver detalles</button>;
  return <button className="min-w-[116px] rounded-lg bg-slate-100 px-4 py-2 text-xs font-medium text-navy transition hover:bg-slate-200">Ver factura</button>;
}
