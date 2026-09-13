import { AppShell } from "@/components/app-shell";
import { PortfolioPageContent } from "@/components/portfolio/portfolio-page";
import { getPortfolioData } from "@/lib/portfolio";

export default async function PortfolioPage() {
  const data = await getPortfolioData();
  return <AppShell activeSection="Portafolio" experience="financier"><PortfolioPageContent data={data}/></AppShell>;
}
