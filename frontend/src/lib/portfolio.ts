import { apiRequest } from "./api";
import { decimalToCents, formatCents } from "./marketplace";

interface ApiPortfolioOperation {
  invoice_folio: string;
  debtor: string;
  capital: string;
  term_days: number;
  status: "pending" | "in_auction" | "funded" | "paid" | "overdue";
  return: string;
}

interface ApiPortfolio {
  financed_capital: string;
  active_operations_count: number;
  recent_operations: ApiPortfolioOperation[];
}

export type PortfolioStatus = "active" | "completed";

export interface PortfolioOperation {
  id: string;
  invoiceFolio: string;
  debtor: string;
  financedCapitalCents: number;
  formattedFinancedCapital: string;
  expectedReturnCents: number;
  formattedExpectedReturn: string;
  financedAt: null;
  formattedFinancedAt: string;
  status: PortfolioStatus;
}

export interface PortfolioData {
  financedCapitalCents: number;
  activeOperationsCount: number;
  expectedReturnCents: null;
  recoveredCapitalCents: null;
  operations: PortfolioOperation[];
}

export async function getPortfolioData(): Promise<PortfolioData> {
  const portfolio = await apiRequest<ApiPortfolio>("/api/financier/portfolio/");
  const operations = portfolio.recent_operations
    .filter((operation) => operation.status === "funded" || operation.status === "paid")
    .map((operation, index) => normalizeOperation(operation, index));

  return {
    financedCapitalCents: decimalToCents(portfolio.financed_capital),
    activeOperationsCount: portfolio.active_operations_count,
    expectedReturnCents: null,
    recoveredCapitalCents: null,
    operations,
  };
}

function normalizeOperation(operation: ApiPortfolioOperation, index: number): PortfolioOperation {
  const financedCapitalCents = decimalToCents(operation.capital);
  const expectedReturnCents = decimalToCents(operation.return);
  return {
    id: `${operation.invoice_folio}-${index}`,
    invoiceFolio: operation.invoice_folio,
    debtor: operation.debtor,
    financedCapitalCents,
    formattedFinancedCapital: formatCents(financedCapitalCents),
    expectedReturnCents,
    formattedExpectedReturn: formatCents(expectedReturnCents),
    financedAt: null,
    formattedFinancedAt: "—",
    status: operation.status === "paid" ? "completed" : "active",
  };
}
