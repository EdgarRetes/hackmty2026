import { AppShell } from "@/components/app-shell";

export default function MarketplaceLoading() {
  return <AppShell activeSection="Marketplace" experience="financier"><div className="mx-auto max-w-[1380px] animate-pulse" aria-label="Cargando Marketplace"><div className="flex justify-between gap-6"><div><div className="h-10 w-60 rounded-lg bg-slate-200"/><div className="mt-3 h-5 w-[480px] max-w-full rounded bg-slate-100"/></div><div className="h-20 w-[365px] rounded-xl bg-slate-100"/></div><div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">{Array.from({ length: 4 }, (_, index) => <div key={index} className="h-[116px] rounded-xl border border-slate-200 bg-white"/>)}</div><div className="mt-4 h-11 rounded-xl bg-slate-100"/><div className="mt-3 h-12 rounded-xl bg-slate-100"/><div className="mt-4 h-[480px] rounded-xl border border-slate-200 bg-white"/></div></AppShell>;
}
