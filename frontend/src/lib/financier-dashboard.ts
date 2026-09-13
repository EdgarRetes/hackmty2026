import { apiRequest } from "./api";
import { decimalToCents, getMarketplaceData, type MarketplaceOpportunity } from "./marketplace";

interface ApiPortfolioOperation {
  invoice_folio: string;
  debtor: string;
  capital: string;
  term_days: number;
  status: "pending" | "in_auction" | "funded" | "paid" | "overdue";
  return: string;
}

interface ApiPortfolio {
  available_capital: string;
  financed_capital: string;
  generated_return: string;
  active_operations_count: number;
  portfolio_by_risk: { low: string; medium: string; high: string };
  capital_history: { month: string; amount: string }[];
  recent_operations: ApiPortfolioOperation[];
}

export interface RecentOperation {
  invoiceFolio: string;
  debtor: string;
  formattedCapital: string;
  termDays: number;
  status: ApiPortfolioOperation["status"];
  formattedReturn: string;
}

export interface CapitalHistoryPoint {
  month: string;
  label: string;
  amountCents: number;
}

// All three amounts are in cents (like every other *Cents field in this
// app) — pass straight into formatCents, never display raw.
export interface PortfolioByRisk {
  low: number;
  medium: number;
  high: number;
}

export interface FinancierDashboardData {
  availableCapitalCents: number | null;
  financedCapitalCents: number | null;
  generatedReturnCents: number | null;
  activeOperationsCount: number | null;
  capitalHistory: CapitalHistoryPoint[] | null;
  recentOperations: RecentOperation[] | null;
  portfolioByRisk: PortfolioByRisk | null;
  opportunities: MarketplaceOpportunity[];
}

export async function getFinancierDashboardData(): Promise<FinancierDashboardData> {
  const [marketplace, portfolio] = await Promise.all([
    getMarketplaceData(),
    apiRequest<ApiPortfolio>("/api/financier/portfolio/"),
  ]);

  const opportunities = [...marketplace.opportunities]
    .sort((a, b) => b.issueDate.localeCompare(a.issueDate) || b.id - a.id)
    .slice(0, 3);

  return {
    availableCapitalCents: decimalToCents(portfolio.available_capital),
    financedCapitalCents: decimalToCents(portfolio.financed_capital),
    generatedReturnCents: decimalToCents(portfolio.generated_return),
    activeOperationsCount: portfolio.active_operations_count,
    capitalHistory: portfolio.capital_history.map((point) => ({
      month: point.month,
      label: formatMonth(point.month),
      amountCents: decimalToCents(point.amount),
    })),
    recentOperations: portfolio.recent_operations.map((operation) => ({
      invoiceFolio: operation.invoice_folio,
      debtor: operation.debtor,
      formattedCapital: `${new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN", maximumFractionDigits: 0 }).format(Number(operation.capital))} MXN`,
      termDays: operation.term_days,
      status: operation.status,
      formattedReturn: `${new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN", maximumFractionDigits: 0 }).format(Number(operation.return))} MXN`,
    })),
    portfolioByRisk: {
      low: decimalToCents(portfolio.portfolio_by_risk.low),
      medium: decimalToCents(portfolio.portfolio_by_risk.medium),
      high: decimalToCents(portfolio.portfolio_by_risk.high),
    },
    opportunities,
  };
}

function formatMonth(value: string): string {
  const [year, month] = value.split("-").map(Number);
  return new Intl.DateTimeFormat("es-MX", { month: "short", year: "2-digit" }).format(new Date(year, month - 1, 1));
}
