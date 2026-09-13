import { AppShell } from "@/components/app-shell";
import { FinancierDashboardContent } from "@/components/financier-dashboard/financier-dashboard-page";
import { getFinancierDashboardData } from "@/lib/financier-dashboard";

export default async function FinancierDashboardPage() {
  const data = await getFinancierDashboardData();
  return <AppShell activeSection="Inicio" experience="financier"><FinancierDashboardContent data={data}/></AppShell>;
}
