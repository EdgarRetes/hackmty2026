import { getMarketplaceData, type MarketplaceOpportunity } from "./marketplace";

export interface FinancierDashboardData {
  availableCapitalCents: number | null;
  financedCapitalCents: number | null;
  generatedReturnCents: number | null;
  activeOperationsCount: number | null;
  capitalHistory: null;
  recentOperations: null;
  portfolioByRisk: null;
  opportunities: MarketplaceOpportunity[];
}

export async function getFinancierDashboardData(): Promise<FinancierDashboardData> {
  const marketplace = await getMarketplaceData();
  const opportunities = [...marketplace.opportunities]
    .sort((a, b) => b.issueDate.localeCompare(a.issueDate) || b.id - a.id)
    .slice(0, 3);

  return {
    availableCapitalCents: marketplace.availableCapitalCents,
    financedCapitalCents: null,
    generatedReturnCents: null,
    activeOperationsCount: null,
    capitalHistory: null,
    recentOperations: null,
    portfolioByRisk: null,
    opportunities,
  };
}
