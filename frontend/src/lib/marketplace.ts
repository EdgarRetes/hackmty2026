import { apiRequest } from "./api";

export type MarketplaceRisk = "low" | "medium" | "high";

interface ApiInvoice {
  id: number;
  folio: string;
  company: { id: number; legal_name: string; rfc: string };
  debtor_client: { id: number; name: string; archetype: string };
  amount: string;
  issue_date: string;
  due_date: string;
  status: "pending" | "in_auction" | "funded" | "paid" | "overdue";
  days_until_due: number;
}

export interface MarketplaceOpportunity {
  id: number;
  folio: string;
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

export async function getMarketplaceData(): Promise<MarketplaceData> {
  const invoices = await apiRequest<ApiInvoice[]>("/api/invoices/");
  const opportunities = invoices
    .filter((invoice) => (invoice.status === "pending" || invoice.status === "in_auction") && invoice.days_until_due > 0)
    .map(normalizeOpportunity);

  return {
    opportunities,
    availableCapitalCents: null,
    knownDebtorsCount: null,
    averageReturnRate: null,
  };
}

function normalizeOpportunity(invoice: ApiInvoice): MarketplaceOpportunity {
  const amountCents = decimalToCents(invoice.amount);
  return {
    id: invoice.id,
    folio: invoice.folio,
    applicant: invoice.company.legal_name,
    debtor: invoice.debtor_client.name,
    debtorInitials: initials(invoice.debtor_client.name),
    amountCents,
    formattedAmount: formatCents(amountCents),
    issueDate: invoice.issue_date,
    formattedIssueDate: formatDate(invoice.issue_date),
    daysUntilDue: invoice.days_until_due,
    risk: null,
    estimatedReturnRate: null,
    estimatedReturnCents: null,
    previouslyFinanced: null,
    sector: null,
  };
}

function decimalToCents(value: string): number {
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
