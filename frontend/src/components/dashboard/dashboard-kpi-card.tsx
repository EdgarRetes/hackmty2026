import { Icon, type IconName } from "../icons";

const tones = { navy: "bg-slate-100 text-navy", green: "bg-[#dcfce7] text-[#16a34a]", orange: "bg-[#fff1dc] text-[#f59e0b]", purple: "bg-[#f3eaff] text-[#7c3aed]" };

export function DashboardKpiCard({ label, value, detail, icon, tone }: { label: string; value: string; detail: string; icon: IconName; tone: keyof typeof tones }) {
  return <article className="flex min-h-[110px] items-center gap-4 rounded-xl border border-slate-200 bg-white px-4 py-4 shadow-[0_7px_22px_rgba(15,31,68,.025)]"><div className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-xl ${tones[tone]}`}><Icon name={icon} size={28}/></div><div className="min-w-0"><p className="text-sm text-[#52688f]">{label}</p><strong className="mt-1 block truncate text-[23px] leading-none tracking-[-.025em] text-navy">{value}</strong><p className="mt-2 text-xs text-[#52688f]">{detail}</p></div></article>;
}
