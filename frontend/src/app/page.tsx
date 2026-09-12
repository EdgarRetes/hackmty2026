import { AppShell } from "@/components/app-shell";
import { DashboardPage } from "@/components/dashboard/dashboard-page";
import { getDashboardData } from "@/lib/dashboard";

export default async function Home() {
  const data = await getDashboardData();
  return <AppShell activeSection="Home"><DashboardPage data={data}/></AppShell>;
}
