"use client";

import { AppShell } from "@/components/app-shell";

export default function InvoicesError({ reset }: { error: Error; reset: () => void }) {
  return <AppShell activeSection="Facturas"><div className="mx-auto max-w-[1380px]"><section className="rounded-xl border border-red-200 bg-white px-6 py-14 text-center"><h1 className="text-2xl font-bold text-navy">No pudimos cargar las facturas</h1><p className="mt-2 text-sm text-[#52688f]">Verifica la conexión con el backend e intenta nuevamente.</p><button onClick={reset} className="mt-5 h-10 rounded-lg bg-navy px-5 text-sm font-semibold text-white">Reintentar</button></section></div></AppShell>;
}
