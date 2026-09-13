import { AppShell } from "@/components/app-shell";

export default function FinancingLoading() {
  return <AppShell activeSection="Financiamientos"><div className="mx-auto max-w-[1380px] animate-pulse" aria-label="Cargando financiamientos"><div className="h-10 w-72 rounded-lg bg-slate-200"/><div className="mt-3 h-5 w-[430px] max-w-full rounded bg-slate-100"/><div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">{Array.from({ length: 4 }, (_, index) => <div key={index} className="h-28 rounded-xl border border-slate-200 bg-white"/>)}</div><div className="mt-5 h-11 rounded-xl bg-slate-100"/><div className="mt-5 h-[480px] rounded-xl border border-slate-200 bg-white"/></div></AppShell>;
}
