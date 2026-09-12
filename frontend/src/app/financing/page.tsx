import { AppShell } from "@/components/app-shell";
import { FinancingPageContent } from "@/components/financing/financing-page";
import { getFinancings } from "@/lib/financing";

export default async function FinancingPage() {
  const financings = await getFinancings();
  return <AppShell activeSection="Financiamientos"><FinancingPageContent financings={financings}/></AppShell>;
}
