import type { InvoiceDetails } from "@/components/offers/data";
import { apiRequest } from "./api";

interface ApiInvoice {
  id: number;
  folio: string;
  debtor_client: { id: number; name: string; archetype: string };
  amount: string;
  due_date: string;
  status: string;
  days_until_due: number;
}

interface ApiPublication {
  id: number;
  company: { id: number; legal_name: string; rfc: string };
  invoices: ApiInvoice[];
  total_amount: string;
  created_at: string;
}

export interface MarketplaceDetailData {
  publication: InvoiceDetails;
  invoices: { id: number; folio: string; client: string; amount: string }[];
  isOpen: boolean;
}

/**
 * The Financiadora-facing view of one publicación: same underlying data
 * as the empresa's own /publications/[batchId] page. Competitor offers are
 * intentionally not requested or exposed to a financier.
 */
export async function getMarketplaceDetail(batchId: string): Promise<MarketplaceDetailData | null> {
  let batch: ApiPublication;
  try {
    batch = await apiRequest<ApiPublication>(`/api/invoice-batches/${encodeURIComponent(batchId)}/`);
  } catch (error) {
    if (error instanceof Error && "status" in error && (error as { status: number }).status === 404) return null;
    throw error;
  }

  const dueDate = batch.invoices.reduce((earliest, invoice) => (invoice.due_date < earliest ? invoice.due_date : earliest), batch.invoices[0].due_date);
  const daysRemaining = Math.min(...batch.invoices.map((invoice) => invoice.days_until_due));
  const isOpen = batch.invoices.some((invoice) => invoice.status === "pending" || invoice.status === "in_auction");

  return {
    publication: {
      id: batch.invoices.length === 1 ? batch.invoices[0].folio : `Publicación #${batch.id}`,
      status: isOpen ? "En subasta" : "Financiada",
      client: [...new Set(batch.invoices.map((invoice) => invoice.debtor_client.name))].join(", "),
      amount: formatMoney(batch.total_amount),
      dueDate: formatDate(dueDate),
      daysRemaining,
    },
    invoices: batch.invoices.map((invoice) => ({
      id: invoice.id,
      folio: invoice.folio,
      client: invoice.debtor_client.name,
      amount: formatMoney(invoice.amount),
    })),
    isOpen,
  };
}

function formatMoney(value: string): string {
  return `${new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN", minimumFractionDigits: 2 }).format(Number(value))} MXN`;
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("es-MX", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" }).format(new Date(`${value}T00:00:00Z`));
}
