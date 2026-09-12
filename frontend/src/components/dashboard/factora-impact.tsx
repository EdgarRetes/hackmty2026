import { formatMoney } from "@/lib/dashboard";
import { Icon } from "../icons";

export function FactoraImpact({ financedAmount }: { financedAmount: number }) {
  return <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-[0_7px_22px_rgba(15,31,68,.025)]"><header className="flex items-center justify-between gap-3"><h2 className="flex items-center gap-2 text-lg font-bold text-navy"><Icon name="arrow" size={20}/>Impacto de Factora</h2><button className="flex h-9 items-center gap-5 rounded-lg border border-slate-200 px-3 text-xs text-navy">Últimos 6 meses <Icon name="chevron" size={14}/></button></header><div className="mt-3 divide-y divide-slate-200"><ImpactRow icon="coins" value={formatMoney(financedAmount)} label="Capital obtenido"/><ImpactRow icon="settings" value="—" label="Ahorro estimado" detail="Sin definición de negocio"/><ImpactRow icon="clock" value="—" label="Tiempo promedio de financiamiento" detail="Sin timestamps suficientes"/></div></section>;
}

function ImpactRow({ icon, value, label, detail = "Comparación no disponible" }: { icon: "coins" | "settings" | "clock"; value: string; label: string; detail?: string }) { return <div className="grid grid-cols-[40px_1fr_auto] items-center gap-3 py-4"><Icon name={icon} size={26}/><div><strong className="text-base text-navy">{value}</strong><p className="mt-0.5 text-xs text-[#52688f]">{label}</p></div><span className="text-right text-[10px] text-[#6b7fa5]">{detail}</span></div>; }
