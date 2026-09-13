import { AppShell } from "@/components/app-shell";

export default function DashboardLoading() {
  return <AppShell activeSection="Home"><div className="mx-auto max-w-[1380px] animate-pulse" aria-label="Cargando dashboard"><div className="h-9 w-72 rounded bg-slate-200"/><div className="mt-3 h-5 w-80 rounded bg-slate-100"/><div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">{Array.from({ length: 4 }, (_, index) => <div key={index} className="h-[110px] rounded-xl border border-slate-200 bg-white"/>)}</div><div className="mt-4 grid gap-4 xl:grid-cols-[1.55fr_1fr]"><div className="h-[360px] rounded-xl border border-slate-200 bg-white"/><div className="h-[360px] rounded-xl border border-slate-200 bg-white"/></div><div className="mt-4 grid gap-4 xl:grid-cols-[1.55fr_1fr]"><div className="h-[300px] rounded-xl border border-slate-200 bg-white"/><div className="h-[300px] rounded-xl border border-slate-200 bg-white"/></div></div></AppShell>;
}
