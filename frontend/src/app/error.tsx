"use client";

import { useEffect } from "react";
import { AppShell } from "@/components/app-shell";

export default function DashboardError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => { console.error(error); }, [error]);
  return <AppShell activeSection="Home"><section className="mx-auto max-w-[1380px] rounded-xl border border-red-200 bg-white px-6 py-14 text-center"><h1 className="text-2xl font-bold text-navy">No pudimos cargar el dashboard</h1><p className="mt-2 text-sm text-[#52688f]">La información financiera no está disponible en este momento.</p><p className="mx-auto mt-3 max-w-2xl break-words rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700">{error.message}{error.digest && <span className="mt-1 block text-[#a3595b]">ID: {error.digest}</span>}</p><button onClick={reset} className="mt-5 h-10 rounded-lg bg-navy px-5 text-sm font-semibold text-white">Reintentar</button></section></AppShell>;
}
