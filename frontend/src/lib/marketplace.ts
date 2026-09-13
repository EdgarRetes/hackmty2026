import { apiRequest } from "./api";

export type MarketplaceRisk = "low" | "medium" | "high";

interface ApiOpportunity {
  id: number;
  folio: string;
  invoice_count: number;
  company: { id: number; legal_name: string; rfc: string };
  debtor: string;
  amount: string;
  issue_date: string;
  due_date: string;
  days_until_due: number;
  sector: string | null;
  risk: MarketplaceRisk;
  estimated_return_rate: string;
  estimated_return: string;
  previously_financed: boolean;
}

interface ApiMarketplaceResponse {
  opportunities: ApiOpportunity[];
  available_capital: string;
}

export interface MarketplaceOpportunity {
  id: number;
  folio: string;
  invoiceCount: number;
  applicant: string;
  debtor: string;
  debtorInitials: string;
  amountCents: number;
  formattedAmount: string;
  issueDate: string;
  formattedIssueDate: string;
  daysUntilDue: number;
  risk: MarketplaceRisk | null;
  estimatedReturnRate: number | null;
  estimatedReturnCents: number | null;
  previouslyFinanced: boolean | null;
  sector: string | null;
}

export interface MarketplaceData {
  opportunities: MarketplaceOpportunity[];
  availableCapitalCents: number | null;
  knownDebtorsCount: number | null;
  averageReturnRate: number | null;
}

/**
 * Each opportunity is a real "publicación" — one or more invoices
 * published together — not a raw invoice. A publication of size 1 is
 * just the single-invoice case; the frontend shape doesn't need to
 * distinguish them.
 */
export async function getMarketplaceData(): Promise<MarketplaceData> {
  const response = await apiRequest<ApiMarketplaceResponse>("/api/marketplace/");
  const opportunities = response.opportunities.map(normalizeOpportunity);

  const knownDebtorsCount = opportunities.filter((item) => item.previouslyFinanced).length;
  const returnRates = opportunities.map((item) => item.estimatedReturnRate).filter((rate): rate is number => rate !== null);
  const averageReturnRate = returnRates.length
    ? Number((returnRates.reduce((sum, rate) => sum + rate, 0) / returnRates.length).toFixed(2))
    : null;

  return {
    opportunities,
    availableCapitalCents: decimalToCents(response.available_capital),
    knownDebtorsCount,
    averageReturnRate,
  };
}

function normalizeOpportunity(opportunity: ApiOpportunity): MarketplaceOpportunity {
  const amountCents = decimalToCents(opportunity.amount);
  return {
    id: opportunity.id,
    folio: opportunity.folio,
    invoiceCount: opportunity.invoice_count,
    applicant: opportunity.company.legal_name,
    debtor: opportunity.debtor,
    debtorInitials: initials(opportunity.debtor),
    amountCents,
    formattedAmount: formatCents(amountCents),
    issueDate: opportunity.issue_date,
    formattedIssueDate: formatDate(opportunity.issue_date),
    daysUntilDue: opportunity.days_until_due,
    risk: opportunity.risk,
    estimatedReturnRate: Number(opportunity.estimated_return_rate),
    estimatedReturnCents: decimalToCents(opportunity.estimated_return),
    previouslyFinanced: opportunity.previously_financed,
    sector: opportunity.sector,
  };
}

export function decimalToCents(value: string): number {
  const [whole = "0", fraction = ""] = value.split(".");
  return Number(whole) * 100 + Number(fraction.padEnd(2, "0").slice(0, 2));
}

export function formatCents(value: number | null): string {
  if (value === null) return "—";
  return new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN", maximumFractionDigits: 2 }).format(value / 100);
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("es-MX", { day: "2-digit", month: "short", year: "numeric", timeZone: "UTC" }).format(new Date(`${value}T00:00:00Z`));
}

function initials(value: string): string {
  return value.split(/\s+/).map((word) => word[0]).join("").slice(0, 2).toUpperCase();
}
