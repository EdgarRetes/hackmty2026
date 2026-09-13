import type { MarketplaceRisk } from "@/lib/marketplace";

const riskStyles: Record<MarketplaceRisk, { label: string; className: string }> = {
  low: { label: "Bajo", className: "bg-[#dcfce7] text-[#16833f]" },
  medium: { label: "Medio", className: "bg-[#fff4d5] text-[#cf7a00]" },
  high: { label: "Alto", className: "bg-[#ffe7eb] text-[#d7263d]" },
};

export function RiskBadge({ risk }: { risk: MarketplaceRisk | null }) {
  if (!risk) return <span className="text-[#6b7fa5]">—</span>;
  const style = riskStyles[risk];
  return <span className={`inline-flex min-w-20 items-center justify-center gap-2 rounded-lg px-3 py-1.5 text-xs font-medium ${style.className}`}><i className="h-2 w-2 rounded-full bg-current"/>{style.label}</span>;
}

export function HistoryBadge({ known }: { known: boolean | null }) {
  if (known === null) return <span className="text-[#6b7fa5]">—</span>;
  return <span className={`inline-flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-medium ${known ? "bg-[#e4faeb] text-[#16833f]" : "bg-[#eef3fb] text-[#526fa9]"}`}><i className="flex h-4 w-4 items-center justify-center rounded-full bg-current text-[9px] text-white">✓</i>{known ? "Financiado previamente" : "Nuevo deudor"}</span>;
}
