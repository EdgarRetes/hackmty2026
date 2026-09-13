import type { InvoiceUiStatus } from "@/lib/invoices";

const statuses: Record<InvoiceUiStatus, { label: string; classes: string; dot: string }> = {
  not_applicable: { label: "No aplica", classes: "bg-slate-100 text-slate-500", dot: "bg-slate-400" },
  available: { label: "Disponible", classes: "bg-[#e6f3ff] text-[#0875d1]", dot: "bg-[#0875d1]" },
  published: { label: "Publicada", classes: "bg-[#f3eaff] text-[#7c3aed]", dot: "bg-[#8b5cf6]" },
  funded: { label: "Financiada", classes: "bg-[#dcfce7] text-[#16a34a]", dot: "bg-[#16a34a]" },
};

export function InvoiceStatusBadge({ status }: { status: InvoiceUiStatus }) {
  const config = statuses[status];
  return <span className={`inline-flex min-w-[108px] items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-medium ${config.classes}`}><i className={`h-2 w-2 rounded-full ${config.dot}`}/>{config.label}</span>;
}
