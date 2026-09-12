import { AppShell } from "@/components/app-shell";
import { OffersPageContent } from "@/components/offers/offers-page";
import { getOffersPageData } from "@/lib/offers";
import { notFound } from "next/navigation";

export default async function OffersPage({ params }: PageProps<"/offers/[invoiceId]">) {
  const { invoiceId } = await params;
  const data = await getOffersPageData(decodeURIComponent(invoiceId));
  if (!data) notFound();
  return <AppShell><OffersPageContent data={data}/></AppShell>;
}
