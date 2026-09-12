import { redirect } from "next/navigation";
import { getDefaultInvoiceReference } from "@/lib/offers";

export default async function Home() {
  const invoiceReference = await getDefaultInvoiceReference();
  if (invoiceReference) redirect(`/offers/${encodeURIComponent(invoiceReference)}`);
  return <main className="flex min-h-screen items-center justify-center bg-[#fbfcfe] p-6"><div className="rounded-xl border border-slate-200 bg-white px-8 py-12 text-center"><h1 className="text-2xl font-bold text-navy">No hay facturas pendientes</h1><p className="mt-2 text-sm text-[#52688f]">Las nuevas facturas aparecerán aquí cuando estén disponibles.</p></div></main>;
}
