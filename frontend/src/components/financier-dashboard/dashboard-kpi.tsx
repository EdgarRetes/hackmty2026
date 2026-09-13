import { Icon, type IconName } from "../icons";

const tones = {
  blue: "bg-[#eaf1ff] text-[#155eef]",
  green: "bg-[#e2f8e8] text-[#0aa44f]",
  violet: "bg-[#f0eaff] text-[#5136df]",
  teal: "bg-[#dcf8f1] text-[#0bad79]",
};

export function DashboardKpi({ label, value, detail, icon, tone }: { label: string; value: string; detail: string; icon: IconName; tone: keyof typeof tones }) {
  return <article className="flex min-h-[120px] items-start gap-4 rounded-xl border border-slate-200 bg-white px-5 py-4 shadow-[0_8px_24px_rgba(15,31,68,.025)]"><span className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-xl ${tones[tone]}`}><Icon name={icon} size={28}/></span><div className="min-w-0 pt-0.5"><p className="text-sm text-[#38517d]">{label}</p><strong className="mt-1 block text-[25px] leading-none text-navy">{value}</strong><p className="mt-2 text-xs leading-4 text-[#1d54b7]">{detail}</p></div></article>;
}
