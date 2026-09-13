import { apiRequest } from "./api";
import { getInvoices, type InvoiceListItem } from "./invoices";
import { decimalToCents } from "./marketplace";

export type FinancierOfferStatus = "pending" | "accepted" | "rejected" | "expired";

export interface FinancierOffer {
  id: number;
  invoiceFolio: string;
  debtor: string;
  invoiceAmountCents: number;
  offeredAmountCents: number;
  offeredReturnRate: number;
  offeredAt: string | null;
  status: FinancierOfferStatus;
}

export interface FinancierOffersData {
  offers: FinancierOffer[];
  totals: Record<FinancierOfferStatus | "all", number | null>;
  collectionAvailable: boolean;
}

interface ApiOffer {
  id: number;
  net_amount: string;
  rate: string;
  expires_at: string;
  is_accepted: boolean;
  accepted_at: string | null;
}

/**
 * The API does not yet expose a current-financier offers collection. Until it
 * does, aggregate the persisted offers exposed by each real invoice. This
 * keeps the page data-driven while preserving the service boundary for a
 * future GET /api/financier/offers/ endpoint.
 */
export async function getFinancierOffersData(): Promise<FinancierOffersData> {
  const invoices = await getInvoices();
  const results = await Promise.allSettled(invoices.filter((invoice) => invoice.offersCount > 0).map(async (invoice) => ({ invoice, offers: await apiRequest<ApiOffer[]>(`/api/invoices/${invoice.id}/offers/`) })));
  const now = Date.now();
  const offers = results.flatMap((result) => result.status === "fulfilled" ? result.value.offers.map((offer) => normalizeOffer(offer, result.value.invoice, now)) : []);
  const totals = { all: offers.length, pending: 0, accepted: 0, rejected: 0, expired: 0 } as Record<FinancierOfferStatus | "all", number>;
  for (const offer of offers) totals[offer.status] += 1;
  return { offers, totals, collectionAvailable: true };
}

function normalizeOffer(offer: ApiOffer, invoice: InvoiceListItem, now: number): FinancierOffer {
  const expiresAt = new Date(offer.expires_at).getTime();
  return {
    id: offer.id,
    invoiceFolio: invoice.folio,
    debtor: invoice.client,
    invoiceAmountCents: Math.round(invoice.amount * 100),
    offeredAmountCents: decimalToCents(offer.net_amount),
    offeredReturnRate: Number(offer.rate),
    // The API has no offer-created field; do not fabricate one.
    offeredAt: offer.accepted_at,
    status: offer.is_accepted ? "accepted" : expiresAt <= now ? "expired" : "pending",
  };
}
