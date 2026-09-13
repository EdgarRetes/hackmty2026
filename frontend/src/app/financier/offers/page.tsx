import { AppShell } from "@/components/app-shell";
import { FinancierOffersPageContent } from "@/components/financier-offers/financier-offers-page";
import { getFinancierOffersData } from "@/lib/financier-offers";

export default async function FinancierOffersPage() {
  const data = await getFinancierOffersData();
  return <AppShell activeSection="Ofertas" experience="financier"><FinancierOffersPageContent data={data}/></AppShell>;
}
