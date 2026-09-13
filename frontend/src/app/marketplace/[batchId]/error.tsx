"use client";

import { AppShell } from "@/components/app-shell";

export default function MarketplaceDetailError({ error, reset }: { error: Error; reset: () => void }) {
  return <AppShell activeSection="Marketplace" experience="financier"><div className="mx-auto max-w-[1280px]"><section className="rounded-xl border border-red-200 bg-white px-6 py-12 text-center"><h1 className="text-2xl font-bold text-navy">No pudimos cargar esta publicación</h1><p className="mt-2 text-sm text-[#52688f]">El backend respondió con un error.</p><p className="mx-auto mt-3 max-w-2xl break-words rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700">{error.message}</p><button type="button" onClick={reset} className="mt-5 h-10 rounded-lg bg-navy px-5 text-sm font-semibold text-white transition hover:bg-[#163361]">Reintentar</button></section></div></AppShell>;
}
