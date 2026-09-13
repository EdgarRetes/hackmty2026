import { AppShell } from "@/components/app-shell";
import { MarketplacePageContent } from "@/components/marketplace/marketplace-page";
import { getMarketplaceData } from "@/lib/marketplace";

export default async function MarketplacePage() {
  const data = await getMarketplaceData();
  return <AppShell activeSection="Marketplace" experience="financier"><MarketplacePageContent data={data}/></AppShell>;
}
