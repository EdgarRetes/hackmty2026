import { Icon, type IconName } from "../icons";

const tones = {
  blue: "bg-[#e2f4ff] text-[#0875d1]",
  orange: "bg-[#fff1dc] text-[#f59e0b]",
  purple: "bg-[#f3eaff] text-[#7c3aed]",
  green: "bg-[#dcfce7] text-[#16a34a]",
};

export function MarketplaceKpiCard({ label, value, detail, icon, tone }: { label: string; value: string; detail: string; icon: IconName; tone: keyof typeof tones }) {
  return <article className="flex min-h-[116px] items-center gap-4 rounded-xl border border-slate-200 bg-white px-4 py-4 shadow-[0_7px_22px_rgba(15,31,68,.025)]"><div className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-xl ${tones[tone]}`}><Icon name={icon} size={28}/></div><div className="min-w-0"><p className="text-sm leading-4 text-[#52688f]">{label}</p><strong className="mt-1.5 block truncate text-[25px] leading-none text-navy">{value}</strong><p className="mt-2 text-xs leading-4 text-[#1d54b7]">{detail}</p></div></article>;
}
