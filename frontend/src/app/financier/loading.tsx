import { AppShell } from "@/components/app-shell";

export default function FinancierDashboardLoading() {
  return <AppShell activeSection="Inicio" experience="financier"><div className="mx-auto max-w-[1380px] animate-pulse"><div className="h-10 w-52 rounded bg-slate-200"/><div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">{Array.from({ length: 4 }, (_, index) => <div key={index} className="h-[120px] rounded-xl bg-slate-200"/>)}</div><div className="mt-4 grid gap-4 xl:grid-cols-2">{Array.from({ length: 4 }, (_, index) => <div key={index} className="h-[290px] rounded-xl bg-slate-200"/>)}</div></div></AppShell>;
}
