import { AppShell } from "@/components/app-shell";

export default function MarketplaceDetailLoading() {
  return <AppShell activeSection="Marketplace" experience="financier"><div className="mx-auto max-w-[1280px] animate-pulse" aria-label="Cargando publicación"><div className="h-10 w-64 rounded-lg bg-slate-200"/><div className="mt-3 h-5 w-96 max-w-full rounded bg-slate-100"/><div className="mt-4 h-28 rounded-xl border border-slate-200 bg-white"/><div className="mt-4 h-24 rounded-xl border border-slate-200 bg-white"/><div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{Array.from({ length: 3 }, (_, index) => <div key={index} className="h-[340px] rounded-xl border border-slate-200 bg-white"/>)}</div></div></AppShell>;
}
