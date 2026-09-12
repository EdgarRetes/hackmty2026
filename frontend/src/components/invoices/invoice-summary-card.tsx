import { Icon, type IconName } from "../icons";

const styles = {
  navy: "bg-slate-100 text-navy",
  gray: "bg-slate-100 text-slate-500",
  purple: "bg-[#f3eaff] text-[#7c3aed]",
  green: "bg-[#dcfce7] text-[#16a34a]",
};

export function InvoiceSummaryCard({ label, count, amount, tone, icon }: { label: string; count: number; amount: string; tone: keyof typeof styles; icon: IconName }) {
  return <article className="flex min-h-[112px] items-center gap-4 rounded-xl border border-slate-200 bg-white px-4 py-4 shadow-[0_7px_22px_rgba(15,31,68,.025)]"><div className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-xl ${styles[tone]}`}><Icon name={icon} size={28}/></div><div><p className="text-sm text-[#52688f]">{label}</p><strong className="mt-1 block text-[25px] leading-none text-navy">{count}</strong><p className="mt-2 text-sm text-[#52688f]">{amount}</p></div></article>;
}
