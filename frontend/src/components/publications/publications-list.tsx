import type { PublicationListItem } from "@/lib/publications";
import { Icon } from "../icons";

export function PublicationsListContent({ publications }: { publications: PublicationListItem[] }) {
  return <div className="mx-auto max-w-[1280px]">
    <h1 className="text-[38px] font-bold leading-none tracking-[-.04em] text-navy">Publicaciones</h1>
    <p className="mt-1.5 text-[17px] text-[#52688f]">Paquetes de facturas que has publicado para conseguir financiamiento.</p>
    {publications.length === 0
      ? <section className="mt-5 rounded-xl border border-dashed border-slate-300 bg-white px-6 py-16 text-center"><h2 className="text-lg font-semibold text-navy">Aún no has publicado ningún paquete.</h2><p className="mt-2 text-sm text-[#52688f]">Selecciona 2 o más facturas en <a href="/invoices" className="font-medium text-[#7c3aed] underline">Facturas</a> y publícalas juntas.</p></section>
      : <section className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">{publications.map((publication) => <a key={publication.id} href={`/publications/${publication.id}`} className="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-5 shadow-[0_8px_24px_rgba(15,31,68,.025)] transition hover:-translate-y-0.5 hover:shadow-lg"><div className="flex items-center justify-between"><span className="flex items-center gap-2 text-sm font-bold text-navy"><Icon name="invoice" size={18}/>Publicación #{publication.id}</span><span className="rounded-lg bg-[#f3eaff] px-2.5 py-1 text-xs font-medium text-[#7c3aed]">{publication.invoiceCount} facturas</span></div><p className="text-[22px] font-bold tracking-[-.03em] text-navy">{publication.totalAmount}</p><p className="text-xs text-[#52688f]">Clientes: {publication.clients.join(", ")}</p><p className="mt-auto text-xs text-[#52688f]">Publicada el {publication.createdAt}</p></a>)}</section>}
  </div>;
}
