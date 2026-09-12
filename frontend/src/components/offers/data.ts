export type OfferTone = "lime" | "blue" | "purple" | "orange";
export interface InvoiceDetails { id: string; status: string; client: string; amount: string; dueDate: string; daysRemaining: number; }
export interface Offer { id: string; financier: string; mark: string; category: string; amount: string; advance: string; advanceValue: number; commission: string; commissionValue: number; cost: string; funding: string; action: string; explanation: string; tone: OfferTone; rank: number; }
export interface OffersPageData { invoice: InvoiceDetails; offers: Offer[]; source: "api"; }
