import type { InvoiceListItem } from "./invoices";
import { getInvoices } from "./invoices";
import { apiRequest } from "./api";

interface DashboardOffer {
  id: number;
  invoice_id: number;
  net_amount: string;
  rank: number;
  expires_at: string;
  is_accepted: boolean;
}

export interface DashboardOpportunity {
  id: string;
  tone: "green" | "purple" | "blue";
  icon: "invoice" | "bars" | "bolt";
  title: string;
  description: string;
  action: string;
  href: string;
}

export interface DashboardData {
  invoices: InvoiceListItem[];
  receivablesAmount: number;
  receivablesCount: number;
  eligibleAmount: number;
  eligibleCount: number;
  activeOffers: number | null;
  invoicesWithActiveOffers: number | null;
  financedAmount: number;
  financedCount: number;
  opportunities: DashboardOpportunity[];
}

export async function getDashboardData(): Promise<DashboardData> {
  const invoices = await getInvoices();
  const receivables = invoices.filter((invoice) => invoice.backendStatus === "pending" || invoice.backendStatus === "available" || invoice.backendStatus === "in_auction");
  const eligible = invoices.filter((invoice) => invoice.backendStatus === "available");
  const financed = invoices.filter((invoice) => invoice.backendStatus === "funded");
  const offerInvoices = invoices.filter((invoice) => invoice.offersCount > 0);
  const offerResults = await Promise.allSettled(offerInvoices.map(async (invoice) => ({ invoice, offers: await apiRequest<DashboardOffer[]>(`/api/invoices/${invoice.id}/offers/`) })));
  const offersAvailable = offerResults.every((result) => result.status === "fulfilled");
  const currentTime = Date.now();
  const activeByInvoice = offerResults.flatMap((result) => result.status === "fulfilled" ? [{ invoice: result.value.invoice, offers: result.value.offers.filter((offer) => !offer.is_accepted && new Date(offer.expires_at).getTime() > currentTime) }] : []);
  const activeOffers = activeByInvoice.flatMap((entry) => entry.offers);

  return {
    invoices,
    receivablesAmount: sumAmounts(receivables),
    receivablesCount: receivables.length,
    eligibleAmount: sumAmounts(eligible),
    eligibleCount: eligible.length,
    activeOffers: offersAvailable ? activeOffers.length : null,
    invoicesWithActiveOffers: offersAvailable ? activeByInvoice.filter((entry) => entry.offers.length > 0).length : null,
    financedAmount: sumAmounts(financed),
    financedCount: financed.length,
    opportunities: buildOpportunities(invoices, activeByInvoice),
  };
}

function buildOpportunities(invoices: InvoiceListItem[], activeByInvoice: { invoice: InvoiceListItem; offers: DashboardOffer[] }[]): DashboardOpportunity[] {
  const opportunities: DashboardOpportunity[] = [];
  const withOffers = activeByInvoice.find((entry) => entry.offers.length > 0);
  if (withOffers) opportunities.push({ id: `offers-${withOffers.invoice.id}`, tone: "green", icon: "invoice", title: `${formatMoney(withOffers.invoice.amount)} disponibles para financiar`, description: `La factura #${withOffers.invoice.folio} tiene ${withOffers.offers.length} ofertas activas.`, action: "Ver ofertas", href: `/offers/${encodeURIComponent(withOffers.invoice.folio)}` });
  const eligible = invoices.find((invoice) => invoice.backendStatus === "available" && invoice.offersCount === 0);
  if (eligible) opportunities.push({ id: `invoice-${eligible.id}`, tone: "purple", icon: "bars", title: "Nueva oportunidad", description: `La factura #${eligible.folio} por ${formatMoney(eligible.amount)} está disponible para el marketplace.`, action: "Ver factura", href: "/invoices" });
  const best = activeByInvoice.flatMap((entry) => entry.offers.map((offer) => ({ offer, invoice: entry.invoice }))).filter((entry) => entry.offer.rank === 1).sort((a, b) => Number(b.offer.net_amount) - Number(a.offer.net_amount))[0];
  if (best) opportunities.push({ id: `best-${best.offer.id}`, tone: "blue", icon: "bolt", title: "Mejor oferta disponible", description: `Puedes recibir ${formatMoney(Number(best.offer.net_amount))} con la factura #${best.invoice.folio}.`, action: "Ver oferta", href: `/offers/${encodeURIComponent(best.invoice.folio)}` });
  return opportunities.slice(0, 3);
}

function sumAmounts(invoices: InvoiceListItem[]) { return invoices.reduce((sum, invoice) => sum + invoice.amount, 0); }
export function formatMoney(amount: number) { return `${new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN", maximumFractionDigits: 2 }).format(amount)} MXN`; }
