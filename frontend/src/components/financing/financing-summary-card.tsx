import { Icon, type IconName } from "../icons";

const styles = {
  blue: "bg-[#e6f3ff] text-[#0875d1]",
  green: "bg-[#dcfce7] text-[#16a34a]",
  purple: "bg-[#f3eaff] text-[#7c3aed]",
};

export function FinancingSummaryCard({ label, value, detail, tone, icon }: { label: string; value: string; detail: string; tone: keyof typeof styles; icon: IconName }) {
  return <article className="flex min-h-[112px] items-center gap-4 rounded-xl border border-slate-200 bg-white px-4 py-4 shadow-[0_7px_22px_rgba(15,31,68,.025)]"><div className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-xl ${styles[tone]}`}><Icon name={icon} size={28}/></div><div className="min-w-0"><p className="text-sm text-[#52688f]">{label}</p><strong className="mt-1 block truncate text-[25px] leading-none text-navy">{value}</strong><p className="mt-2 truncate text-sm text-[#52688f]">{detail}</p></div></article>;
}
