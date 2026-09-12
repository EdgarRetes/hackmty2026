import { apiRequest } from "./api";

export type InvoiceUiStatus = "not_applicable" | "published" | "funded";

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
  offers_count: number;
}

export interface InvoiceListItem {
  id: number;
  folio: string;
  client: string;
  amount: number;
  formattedAmount: string;
  issueDate: string;
  formattedIssueDate: string;
  backendStatus: ApiInvoice["status"];
  status: InvoiceUiStatus;
  offersCount: number;
}

export async function getInvoices(): Promise<InvoiceListItem[]> {
  const invoices = await apiRequest<ApiInvoice[]>("/api/invoices/");
  return invoices.map(normalizeInvoice);
}

function normalizeInvoice(invoice: ApiInvoice): InvoiceListItem {
  const amount = Number(invoice.amount);
  return {
    id: invoice.id,
    folio: invoice.folio,
    client: invoice.debtor_client.name,
    amount,
    formattedAmount: `${new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN", maximumFractionDigits: 2 }).format(amount)} MXN`,
    issueDate: invoice.issue_date,
    formattedIssueDate: new Intl.DateTimeFormat("es-MX", { day: "2-digit", month: "short", year: "numeric", timeZone: "UTC" }).format(new Date(`${invoice.issue_date}T00:00:00Z`)),
    backendStatus: invoice.status,
    status: mapStatus(invoice.status, invoice.offers_count),
    offersCount: invoice.offers_count,
  };
}

function mapStatus(status: ApiInvoice["status"], offersCount: number): InvoiceUiStatus {
  if (status === "in_auction" || (status === "pending" && offersCount > 0)) return "published";
  if (status === "funded") return "funded";
  return "not_applicable";
}
