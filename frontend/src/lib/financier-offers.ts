export type FinancierOfferStatus = "pending" | "accepted" | "rejected" | "expired";

export interface FinancierOffer {
  id: number;
  invoiceFolio: string;
  debtor: string;
  invoiceAmountCents: number;
  offeredAmountCents: number;
  offeredReturnRate: number;
  offeredAt: string;
  status: FinancierOfferStatus;
}

export interface FinancierOffersData {
  offers: FinancierOffer[];
  totals: Record<FinancierOfferStatus | "all", number | null>;
  collectionAvailable: boolean;
}

/**
 * The backend currently exposes offers only per invoice and does not expose a
 * current-financier offers collection or a rejected state. Keep this boundary
 * isolated so it can be replaced by GET /api/financier/offers/ later without
 * changing the page components.
 */
export async function getFinancierOffersData(): Promise<FinancierOffersData> {
  return {
    offers: [],
    totals: { all: null, pending: null, accepted: null, rejected: null, expired: null },
    collectionAvailable: false,
  };
}
