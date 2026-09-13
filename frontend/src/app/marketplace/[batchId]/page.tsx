import { AppShell } from "@/components/app-shell";
import { MarketplacePublicationDetail } from "@/components/marketplace/publication-detail-page";
import { getMarketplaceDetail } from "@/lib/marketplace-detail";
import { notFound } from "next/navigation";

export default async function MarketplacePublicationPage({ params }: { params: Promise<{ batchId: string }> }) {
  const { batchId } = await params;
  const data = await getMarketplaceDetail(decodeURIComponent(batchId));
  if (!data) notFound();
  return <AppShell activeSection="Marketplace" experience="financier"><MarketplacePublicationDetail batchId={Number(batchId)} data={data}/></AppShell>;
}
