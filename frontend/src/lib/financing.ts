import { apiRequest } from "./api";
import { getInvoices } from "./invoices";

export type FinancingUiStatus = "active" | "completed" | "cancelled";

interface ApiOffer {
  id: number;
  invoice_id: number;
  lender: { id: number; name: string; risk_profile: string };
  net_amount: string;
  is_accepted: boolean;
  accepted_at?: string | null;
}

export interface FinancingListItem {
  id: number;
  invoiceId: number;
  invoiceFolio: string;
  lender: string;
  receivedAmount: number;
  formattedReceivedAmount: string;
  startedAt: string | null;
  formattedStartedAt: string;
  status: FinancingUiStatus;
  outstandingAmount: number | null;
  formattedOutstandingAmount: string;
}

/**
 * Accepted offers are the backend's current source of truth for financings.
 * The backend does not yet model repayment, cancellation, or outstanding balance.
 */
export async function getFinancings(): Promise<FinancingListItem[]> {
  const invoices = await getInvoices();
  const financedInvoices = invoices.filter((invoice) => invoice.backendStatus === "funded" || invoice.backendStatus === "paid");

  const financingGroups = await Promise.all(financedInvoices.map(async (invoice) => {
    const offers = await apiRequest<ApiOffer[]>(`/api/invoices/${invoice.id}/offers/`);
    return offers
      .filter((offer) => offer.is_accepted)
      .map((offer) => normalizeFinancing(offer, invoice.folio, invoice.backendStatus === "paid" ? "completed" : "active"));
  }));

  return financingGroups.flat().sort(compareNewest);
}

function normalizeFinancing(offer: ApiOffer, invoiceFolio: string, status: FinancingUiStatus): FinancingListItem {
  const receivedAmount = Number(offer.net_amount);
  const startedAt = offer.accepted_at ?? null;
  return {
    id: offer.id,
    invoiceId: offer.invoice_id,
    invoiceFolio,
    lender: offer.lender.name,
    receivedAmount,
    formattedReceivedAmount: formatMoney(receivedAmount),
    startedAt,
    formattedStartedAt: startedAt ? formatDate(startedAt) : "—",
    status,
    outstandingAmount: null,
    formattedOutstandingAmount: "—",
  };
}

function compareNewest(a: FinancingListItem, b: FinancingListItem): number {
  if (!a.startedAt && !b.startedAt) return b.id - a.id;
  if (!a.startedAt) return 1;
  if (!b.startedAt) return -1;
  return b.startedAt.localeCompare(a.startedAt);
}

export function formatFinancingMoney(value: number): string {
  return formatMoney(value);
}

function formatMoney(value: number): string {
  return `${new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN", maximumFractionDigits: 2 }).format(value)} MXN`;
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("es-MX", { day: "2-digit", month: "short", year: "numeric", timeZone: "America/Mexico_City" }).format(new Date(value));
}
