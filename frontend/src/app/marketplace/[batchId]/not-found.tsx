import { AppShell } from "@/components/app-shell";

export default function MarketplaceDetailNotFound() {
  return <AppShell activeSection="Marketplace" experience="financier"><div className="mx-auto max-w-[1280px]"><section className="rounded-xl border border-slate-200 bg-white px-6 py-12 text-center"><h1 className="text-2xl font-bold text-navy">Publicación no encontrada</h1><p className="mt-2 text-sm text-[#52688f]">No existe una publicación con este identificador o ya no está disponible.</p></section></div></AppShell>;
}
