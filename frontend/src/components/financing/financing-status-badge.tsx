import type { FinancingUiStatus } from "@/lib/financing";

const statuses: Record<FinancingUiStatus, { label: string; style: string }> = {
  active: { label: "Activo", style: "bg-[#e6f3ff] text-[#0875d1]" },
  completed: { label: "Completado", style: "bg-[#dcfce7] text-[#169447]" },
  cancelled: { label: "Cancelado", style: "bg-[#ffe7eb] text-[#dc263b]" },
};

export function FinancingStatusBadge({ status }: { status: FinancingUiStatus }) {
  const item = statuses[status];
  return <span className={`inline-flex min-w-[112px] items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-medium ${item.style}`}><i className="h-2 w-2 rounded-full bg-current"/>{item.label}</span>;
}
