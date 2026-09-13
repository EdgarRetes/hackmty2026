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

export interface PublicationListItem {
  id: number;
  invoiceCount: number;
  totalAmount: string;
  createdAt: string;
  clients: string[];
}

export interface PublicationPageData {
  publication: InvoiceDetails;
  invoices: { id: number; folio: string; client: string; amount: string }[];
  offers: Offer[];
}

/**
 * Publishes several of the empresa's own pending invoices together as one
 * package (a "publicación"/batch) a financiadora can fund as a whole.
 */
export async function createPublication(invoiceIds: number[], termDays = 30): Promise<{ id: number }> {
  return apiRequest<ApiPublication>("/api/invoice-batches/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ invoice_ids: invoiceIds, term_days: termDays }),
  });
}

export type PackagePreview = { candidates: { id: number; folio: string; amount: string; net_disbursement: string; expected_loss: string }[]; recommendation: { invoice_ids: number[]; net_disbursement: string; expected_loss: string; target_reached: boolean; shortfall: string; excess: string } | null };
export async function previewPackage(termDays: number, liquidityTarget?: string): Promise<PackagePreview> {
  return apiRequest<PackagePreview>("/api/invoice-batches/preview/", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(liquidityTarget ? { term_days: termDays, mode: "liquidity_target", liquidity_target: liquidityTarget } : { term_days: termDays, mode: "manual" }) });
}

export async function getPublications(): Promise<PublicationListItem[]> {
  const batches = await apiRequest<ApiPublication[]>("/api/invoice-batches/");
  return batches.map((batch) => ({
    id: batch.id,
    invoiceCount: batch.invoices.length,
    totalAmount: formatMoney(batch.total_amount),
    createdAt: formatDate(batch.created_at.slice(0, 10)),
    clients: [...new Set(batch.invoices.map((invoice) => invoice.debtor_client.name))],
  }));
}

export async function getPublicationPageData(batchId: string): Promise<PublicationPageData | null> {
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

  return {
    publication: {
      id: `Publicación #${batch.id}`,
      status: "Publicada",
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
    offers: mapOffers(apiOffers),
  };
}

function mapOffers(apiOffers: ApiBatchOffer[]): Offer[] {
  return apiOffers.map((offer, index) => {
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
      // Batch offers aren't backed by a real, persisted Offer id yet, so
      // there's no accept action here — see API_CONTRACT.md. Never mark
      // one "Aceptar oferta" (that label is what triggers OfferCard's
      // accept call elsewhere in the app).
      action: "Ver detalles",
      explanation: classification.explanation,
      tone: classification.tone,
      rank: offer.rank ?? index,
    };
  });
}

function classifyOffer(category: ApiBatchOffer["category"]) {
  const categories = {
    best: { category: "Mejor oferta", explanation: "Primera opción según el ranking calculado por el backend para este paquete.", tone: "lime" as const },
    lowest_rate: { category: "Menor comisión", explanation: "La propuesta con la tasa más baja para este paquete de facturas.", tone: "blue" as const },
    highest_advance: { category: "Mayor anticipo", explanation: "La propuesta con el mayor porcentaje de anticipo para este paquete.", tone: "purple" as const },
    fastest: { category: "Más rápido", explanation: "La propuesta con el desembolso más rápido para este paquete.", tone: "orange" as const },
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
