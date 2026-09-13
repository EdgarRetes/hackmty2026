export type OfferTone = "lime" | "blue" | "purple" | "orange";
export interface InvoiceDetails { id: string; status: string; client: string; amount: string; dueDate: string; daysRemaining: number; }
export interface Offer { id: string; lenderId: number; financier: string; mark: string; category: string; amount: string; advance: string; advanceValue: number; commission: string; commissionValue: number; cost: string; funding: string; action: string; explanation: string; tone: OfferTone; rank: number; }
export interface RiskAssessment {
  decision: "APPROVE" | "REVIEW" | "REJECT";
  rating: string;
  score: string;
  probabilityOfDefault: string;
  lossGivenDefault: string;
  expectedLoss: string;
  monthlyRate: string;
  termDays: number;
  expectedProfit: string;
  confidence: string;
  reasons: string[];
  warnings: string[];
  policyVersion: string;
  referenceRateAsOf: string;
  referenceRateSource: string;
}
export interface OffersPageData { invoice: InvoiceDetails; offers: Offer[]; riskAssessment: RiskAssessment; source: "api"; }
