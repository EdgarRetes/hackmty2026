import type { InvoiceDetails, Offer, OfferTone, OffersPageData, RiskAssessment } from "@/components/offers/data";
import { ApiError, apiRequest } from "./api";

interface ApiInvoice {
  id: number;
  folio: string;
  debtor_client: { id: number; name: string; archetype: string };
  amount: string;
  due_date: string;
  status: string;
  days_until_due: number;
}

interface ApiOffer {
  id: number;
  invoice_id: number;
  lender: { id: number; name: string; risk_profile: string };
  advance_percentage: string;
  rate: string;
  net_amount: string;
  financing_cost: string;
  funding_time: string;
  category: "best" | "lowest_rate" | "highest_advance" | "fastest";
  rank: number;
  expires_at: string;
  is_accepted: boolean;
}

interface AcceptOfferResponse {
  offer_id: number;
  invoice_id: number;
  status: "accepted";
  transaction_id: string;
  accepted_at: string;
  settlement_date: string;
}

interface ApiRiskAssessment {
  decision: "APPROVE" | "REVIEW" | "REJECT";
  rating: string;
  risk_score: string;
  probability_of_default: string;
  loss_given_default: string;
  expected_loss: string;
  recommended_monthly_rate: string;
  term_days: number;
  expected_investor_profit: string;
  confidence: string;
  reasons: string[];
  warnings: string[];
  policy_version: string;
  reference_rate_as_of: string;
  reference_rate_source: string;
}

/**
 * Frontend data boundary for the Offers route.
 *
 * Maps the current Django API contract into presentation-ready values. It never
 * falls back to local data: upstream errors and empty arrays remain observable.
 */
export async function getOffersPageData(invoiceId: string): Promise<OffersPageData | null> {
  let invoice: ApiInvoice;
  try {
    invoice = await apiRequest<ApiInvoice>(`/api/invoices/${encodeURIComponent(invoiceId)}/`);
  } catch (error) {
    if (error instanceof Error && "status" in error && error.status === 404) return null;
    throw error;
  }

  let apiOffers: ApiOffer[] = [];
  let assessment: ApiRiskAssessment;
  try {
    apiOffers = await apiRequest<ApiOffer[]>(`/api/invoices/${invoice.id}/offers/`, { method: "POST" });
    assessment = await apiRequest<ApiRiskAssessment>(`/api/invoices/${invoice.id}/risk-assessment/`);
  } catch (error) {
    if (!(error instanceof ApiError) || error.status !== 422) throw error;
    const body = JSON.parse(error.body) as { assessment: ApiRiskAssessment };
    assessment = body.assessment;
  }
  return {
    invoice: mapInvoice(invoice),
    offers: mapOffers(apiOffers),
    riskAssessment: mapRiskAssessment(assessment),
    source: "api",
  };
}

function mapRiskAssessment(assessment: ApiRiskAssessment): RiskAssessment {
  return {
    decision: assessment.decision,
    rating: assessment.rating,
    score: formatDecimal(assessment.risk_score),
    probabilityOfDefault: formatPercentFraction(assessment.probability_of_default),
    lossGivenDefault: formatPercentFraction(assessment.loss_given_default),
    expectedLoss: formatMoney(assessment.expected_loss),
    monthlyRate: formatPercentFraction(assessment.recommended_monthly_rate),
    termDays: assessment.term_days,
    expectedProfit: formatMoney(assessment.expected_investor_profit),
    confidence: assessment.confidence,
    reasons: assessment.reasons,
    warnings: assessment.warnings,
    policyVersion: assessment.policy_version,
    referenceRateAsOf: formatDate(assessment.reference_rate_as_of),
    referenceRateSource: assessment.reference_rate_source,
  };
}

export async function getDefaultInvoiceReference(): Promise<string | null> {
  const invoices = await apiRequest<ApiInvoice[]>("/api/invoices/");
  return invoices.find((invoice) => invoice.status === "pending" || invoice.status === "in_auction")?.folio ?? null;
}

export async function acceptOffer(offerId: string): Promise<AcceptOfferResponse> {
  return apiRequest<AcceptOfferResponse>(`/api/offers/${encodeURIComponent(offerId)}/accept/`, { method: "POST" });
}

function mapInvoice(invoice: ApiInvoice): InvoiceDetails {
  return {
    id: invoice.folio,
    status: statusLabel(invoice.status),
    client: invoice.debtor_client.name,
    amount: formatMoney(invoice.amount),
    dueDate: formatDate(invoice.due_date),
    daysRemaining: invoice.days_until_due,
  };
}

function mapOffers(apiOffers: ApiOffer[]): Offer[] {
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
      action: index === 0 ? "Aceptar oferta" : "Ver detalles",
      explanation: classification.explanation,
      tone: classification.tone,
      rank: offer.rank ?? index,
    };
  });
}

function classifyOffer(category: ApiOffer["category"]): { category: string; explanation: string; tone: OfferTone } {
  const categories = {
    best: { category: "Mejor oferta", explanation: "Primera opción según el ranking calculado por el backend.", tone: "lime" },
    lowest_rate: { category: "Menor comisión", explanation: "La propuesta con la tasa más baja entre las ofertas recibidas.", tone: "blue" },
    highest_advance: { category: "Mayor anticipo", explanation: "La propuesta con el mayor porcentaje de anticipo.", tone: "purple" },
    fastest: { category: "Más rápido", explanation: "La propuesta con el desembolso más rápido.", tone: "orange" },
  } satisfies Record<ApiOffer["category"], { category: string; explanation: string; tone: OfferTone }>;
  return categories[category];
}

function formatMoney(value: string): string {
  return `${new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN", minimumFractionDigits: 2 }).format(Number(value))} MXN`;
}

function formatDecimal(value: string): string {
  return new Intl.NumberFormat("es-MX", { maximumFractionDigits: 2 }).format(Number(value));
}

function formatPercentFraction(value: string): string {
  return `${new Intl.NumberFormat("es-MX", { maximumFractionDigits: 2 }).format(Number(value) * 100)}%`;
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("es-MX", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" }).format(new Date(`${value}T00:00:00Z`));
}

function initials(name: string): string {
  return name.split(/\s+/).map((word) => word[0]).join("").slice(0, 2).toUpperCase();
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = { pending: "Pendiente", in_auction: "En subasta", funded: "Financiada", paid: "Pagada", overdue: "Vencida" };
  return labels[status] ?? status;
}
