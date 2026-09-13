"use client";

import { AppShell } from "@/components/app-shell";

export default function DashboardError({ reset }: { error: Error; reset: () => void }) {
  return <AppShell activeSection="Home"><section className="mx-auto max-w-[1380px] rounded-xl border border-red-200 bg-white px-6 py-14 text-center"><h1 className="text-2xl font-bold text-navy">No pudimos cargar el dashboard</h1><p className="mt-2 text-sm text-[#52688f]">La información financiera no está disponible en este momento.</p><button onClick={reset} className="mt-5 h-10 rounded-lg bg-navy px-5 text-sm font-semibold text-white">Reintentar</button></section></AppShell>;
}
