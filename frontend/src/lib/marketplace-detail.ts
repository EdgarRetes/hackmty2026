import type { InvoiceDetails, Offer } from "@/components/offers/data";
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

interface ApiBatchOffer {
  id: number;
  batch_id: number;
  lender: { id: number; name: string; risk_profile: string };
  advance_percentage: string;
  rate: string;
  net_amount: string;
  financing_cost: string;
  funding_time: string;
  category: "best" | "lowest_rate" | "highest_advance" | "fastest";
  rank: number;
  expires_at: string;
}

export interface AcceptPublicationResponse {
  batch_id: number;
  lender_id: number;
  status: "accepted";
  invoices_funded: number;
  total_net_amount: string;
  transaction_id: string;
  accepted_at: string;
}

export interface MarketplaceDetailData {
  publication: InvoiceDetails;
  invoices: { id: number; folio: string; client: string; amount: string }[];
  offers: Offer[];
  isOpen: boolean;
}

/**
 * The Financiadora-facing view of one publicación: same underlying data
 * as the empresa's own /publications/[batchId] page, but offers are
 * marked actionable ("Hacer oferta") when the publication is still open,
 * since here the viewer is the one deciding whether to fund it.
 */
export async function getMarketplaceDetail(batchId: string): Promise<MarketplaceDetailData | null> {
  let batch: ApiPublication;
  try {
    batch = await apiRequest<ApiPublication>(`/api/invoice-batches/${encodeURIComponent(batchId)}/`);
  } catch (error) {
    if (error instanceof Error && "status" in error && (error as { status: number }).status === 404) return null;
    throw error;
  }

  const apiOffers = await apiRequest<ApiBatchOffer[]>(`/api/invoice-batches/${batch.id}/offers/`);
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
    offers: apiOffers.map((offer) => mapOffer(offer, isOpen)),
    isOpen,
  };
}

export async function acceptPublication(batchId: number, lenderId: number): Promise<AcceptPublicationResponse> {
  return apiRequest<AcceptPublicationResponse>(`/api/invoice-batches/${batchId}/accept/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lender_id: lenderId }),
  });
}

function mapOffer(offer: ApiBatchOffer, isOpen: boolean): Offer {
  const classification = classifyOffer(offer.category);
  return {
    id: String(offer.id),
    lenderId: offer.lender.id,
    financier: offer.lender.name,
    mark: initials(offer.lender.name),
    category: classification.category,
    amount: formatMoney(offer.net_amount),
    advance: `${formatDecimal(offer.advance_percentage)}%`,
    advanceValue: Number(offer.advance_percentage),
    commission: `${formatDecimal(offer.rate)}%`,
    commissionValue: Number(offer.rate),
    cost: formatMoney(offer.financing_cost),
    funding: offer.funding_time,
    action: isOpen ? "Hacer oferta" : "Ver detalles",
    explanation: classification.explanation,
    tone: classification.tone,
    rank: offer.rank,
  };
}

function classifyOffer(category: ApiBatchOffer["category"]) {
  const categories = {
    best: { category: "Mejor retorno", explanation: "La combinación de anticipo y tasa más favorable para ti en esta publicación.", tone: "lime" as const },
    lowest_rate: { category: "Menor comisión", explanation: "La tasa más baja de las tres estrategias para esta publicación.", tone: "blue" as const },
    highest_advance: { category: "Mayor anticipo", explanation: "El porcentaje de anticipo más alto para esta publicación.", tone: "purple" as const },
    fastest: { category: "Más rápido", explanation: "El desembolso más rápido para esta publicación.", tone: "orange" as const },
  };
  return categories[category];
}

function formatMoney(value: string): string {
  return `${new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN", minimumFractionDigits: 2 }).format(Number(value))} MXN`;
}

function formatDecimal(value: string): string {
  return new Intl.NumberFormat("es-MX", { maximumFractionDigits: 2 }).format(Number(value));
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("es-MX", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" }).format(new Date(`${value}T00:00:00Z`));
}

function initials(name: string): string {
  return name.split(/\s+/).map((word) => word[0]).join("").slice(0, 2).toUpperCase();
}
