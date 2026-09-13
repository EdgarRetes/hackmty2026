"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { Icon } from "@/components/icons";
import {
  createPublication,
  previewPackage,
  type PackagePreview,
} from "@/lib/publications";

import { summarizePackage } from "./package-builder-state";

type Candidate = PackagePreview["candidates"][number];

const TERMS = [30, 60, 90] as const;
const money = new Intl.NumberFormat("es-MX", {
  style: "currency",
  currency: "MXN",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

export function PackageBuilder() {
  const router = useRouter();
  const [term, setTerm] = useState<(typeof TERMS)[number]>(30);
  const [target, setTarget] = useState("");
  const [data, setData] = useState<PackagePreview | null>(null);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCalculating, setIsCalculating] = useState(false);
  const [isPublishing, setIsPublishing] = useState(false);
  const [hasRecommendation, setHasRecommendation] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    previewPackage(term)
      .then((result) => {
        if (active) setData(result);
      })
      .catch((requestError: Error) => {
        if (active) setError(requestError.message);
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });
    return () => {
      active = false;
    };
  }, [term]);

  const targetAmount = parseMoneyInput(target);
  const selected = useMemo(
    () => data?.candidates.filter((candidate) => selectedIds.includes(candidate.id)) ?? [],
    [data, selectedIds],
  );
  const available = useMemo(
    () => data?.candidates.filter((candidate) => !selectedIds.includes(candidate.id)) ?? [],
    [data, selectedIds],
  );
  const summary = useMemo(
    () => summarizePackage(data?.candidates ?? [], selectedIds, targetAmount),
    [data, selectedIds, targetAmount],
  );

  function selectTerm(nextTerm: (typeof TERMS)[number]) {
    setIsLoading(true);
    setError("");
    setTerm(nextTerm);
    setSelectedIds([]);
    setHasRecommendation(false);
  }

  async function calculateRecommendation() {
    if (targetAmount <= 0) return;
    setIsCalculating(true);
    setError("");
    try {
      const result = await previewPackage(term, targetAmount.toFixed(2));
      setData(result);
      setSelectedIds(result.recommendation?.invoice_ids ?? []);
      setHasRecommendation(true);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "No pudimos calcular la combinación. Intenta de nuevo.",
      );
    } finally {
      setIsCalculating(false);
    }
  }

  function addInvoice(invoiceId: number) {
    setSelectedIds((current) => [...current, invoiceId]);
  }

  function removeInvoice(invoiceId: number) {
    setSelectedIds((current) => current.filter((id) => id !== invoiceId));
  }

  async function publishPackage() {
    if (!selectedIds.length) return;
    setIsPublishing(true);
    setError("");
    try {
      const batch = await createPublication(selectedIds, term);
      router.push(`/publications/${batch.id}`);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "No pudimos publicar el paquete. Tu selección sigue guardada.",
      );
      setIsPublishing(false);
    }
  }

  return (
    <div className="mx-auto max-w-[1380px] pb-10">
      <header>
        <button
          type="button"
          onClick={() => router.push("/invoices")}
          className="group inline-flex items-center gap-1.5 text-sm font-medium text-[#52688f] outline-none transition hover:text-navy focus-visible:rounded-md focus-visible:ring-2 focus-visible:ring-navy/30"
        >
          <Icon name="chevronLeft" size={17} />
          Facturas
          <span className="text-slate-300">/</span>
          <span className="text-navy">Nuevo paquete</span>
        </button>
        <div className="mt-4 max-w-3xl">
          <h1 className="text-[36px] font-bold leading-[1.05] tracking-[-.03em] text-navy sm:text-[40px]">
            Crea tu paquete de factoraje
          </h1>
          <p className="mt-2 max-w-[68ch] text-[16px] leading-6 text-[#52688f]">
            Dinos cuánto efectivo necesitas y encontraremos la combinación de facturas con menor pérdida esperada.
          </p>
        </div>
      </header>

      <LiquidityConfigurator
        term={term}
        target={target}
        targetAmount={targetAmount}
        isCalculating={isCalculating}
        onTargetChange={setTarget}
        onTermChange={selectTerm}
        onCalculate={calculateRecommendation}
      />

      {error ? (
        <div role="alert" className="mt-4 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          <span className="mt-0.5 grid size-5 shrink-0 place-items-center rounded-full bg-red-100 font-bold">!</span>
          <div><strong>No pudimos completar la acción.</strong><p className="mt-0.5 text-red-700">{error}</p></div>
        </div>
      ) : null}

      <div className="mt-5 grid items-start gap-5 xl:grid-cols-[minmax(0,1fr)_340px]">
        <main className="min-w-0 space-y-5">
          <PackageResult
            hasRecommendation={hasRecommendation}
            targetAmount={targetAmount}
            summary={summary}
          />
          <SelectedInvoices
            invoices={selected}
            isLoading={isLoading}
            hasRecommendation={hasRecommendation}
            onRemove={removeInvoice}
          />
          <AvailableInvoices invoices={available} isLoading={isLoading} onAdd={addInvoice} />
        </main>
        <PublishSummary
          term={term}
          targetAmount={targetAmount}
          summary={summary}
          isPublishing={isPublishing}
          onPublish={publishPackage}
        />
      </div>
    </div>
  );
}

function LiquidityConfigurator({
  term,
  target,
  targetAmount,
  isCalculating,
  onTargetChange,
  onTermChange,
  onCalculate,
}: {
  term: (typeof TERMS)[number];
  target: string;
  targetAmount: number;
  isCalculating: boolean;
  onTargetChange: (value: string) => void;
  onTermChange: (term: (typeof TERMS)[number]) => void;
  onCalculate: () => void;
}) {
  return (
    <section className="mt-6 overflow-hidden rounded-2xl bg-navy text-white shadow-[0_16px_36px_rgba(11,31,68,.16)]">
      <div className="grid gap-6 px-5 py-6 sm:px-7 lg:grid-cols-[minmax(0,1.15fr)_minmax(260px,.7fr)_auto] lg:items-end lg:px-8 lg:py-7">
        <label className="block">
          <span className="text-sm font-semibold text-white">¿Cuánto efectivo necesitas?</span>
          <span className="mt-1 block text-xs leading-5 text-[#b8c7e1]">Usaremos esta meta para optimizar tu combinación.</span>
          <span className="mt-3 flex h-14 items-center rounded-xl bg-white px-4 text-navy shadow-[0_4px_14px_rgba(0,0,0,.14)] focus-within:ring-2 focus-within:ring-lime">
            <span className="mr-2 text-lg font-semibold text-[#52688f]">$</span>
            <input
              value={target}
              onChange={(event) => onTargetChange(event.target.value)}
              onKeyDown={(event) => { if (event.key === "Enter" && targetAmount > 0) onCalculate(); }}
              inputMode="decimal"
              aria-label="Efectivo necesario en pesos mexicanos"
              placeholder="250,000"
              className="min-w-0 flex-1 bg-transparent text-xl font-bold tracking-[-.02em] outline-none placeholder:text-slate-300"
            />
            <span className="text-xs font-semibold text-[#52688f]">MXN</span>
          </span>
        </label>

        <fieldset>
          <legend className="text-sm font-semibold text-white">Plazo de factoraje</legend>
          <p className="mt-1 text-xs leading-5 text-[#b8c7e1]">El costo estimado cambia con el plazo.</p>
          <div className="mt-3 grid h-14 grid-cols-3 rounded-xl bg-[#17315f] p-1" role="radiogroup">
            {TERMS.map((days) => (
              <button
                key={days}
                type="button"
                role="radio"
                aria-checked={term === days}
                onClick={() => onTermChange(days)}
                className={`rounded-lg text-sm font-semibold outline-none transition focus-visible:ring-2 focus-visible:ring-lime ${term === days ? "bg-white text-navy shadow-sm" : "text-[#cfdaed] hover:bg-white/8 hover:text-white"}`}
              >
                {days} días
              </button>
            ))}
          </div>
        </fieldset>

        <button
          type="button"
          disabled={targetAmount <= 0 || isCalculating}
          onClick={onCalculate}
          className="inline-flex h-14 items-center justify-center gap-2 rounded-xl bg-lime px-6 text-sm font-bold text-navy outline-none transition hover:bg-[#e0f88a] focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-navy disabled:cursor-not-allowed disabled:bg-[#70809c] disabled:text-[#d9e0eb]"
        >
          <Icon name={isCalculating ? "clock" : "bolt"} size={18} />
          {isCalculating ? "Calculando..." : "Calcular combinación"}
        </button>
      </div>
    </section>
  );
}

function PackageResult({
  hasRecommendation,
  targetAmount,
  summary,
}: {
  hasRecommendation: boolean;
  targetAmount: number;
  summary: ReturnType<typeof summarizePackage>;
}) {
  const targetReached = targetAmount > 0 && summary.shortfall === 0;
  return (
    <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
      <div className="grid gap-5 px-5 py-5 sm:px-6 lg:grid-cols-[1.2fr_1fr] lg:items-center">
        <div>
          <div className="flex items-center gap-2 text-sm font-semibold text-[#52688f]">
            <span className="grid size-8 place-items-center rounded-lg bg-[#eff4fa] text-navy"><Icon name="wallet" size={18} /></span>
            Efectivo estimado a recibir
          </div>
          <p className="mt-3 text-[34px] font-bold leading-none tracking-[-.03em] text-navy sm:text-[40px]" aria-live="polite">
            {money.format(summary.estimatedCash)}
          </p>
          <p className="mt-2 text-sm text-[#52688f]">
            {summary.invoiceCount ? `${summary.invoiceCount} factura${summary.invoiceCount === 1 ? "" : "s"} en la selección actual` : "Agrega facturas o calcula una combinación para comenzar."}
          </p>
        </div>
        <div className="border-t border-slate-100 pt-5 lg:border-l lg:border-t-0 lg:pl-6 lg:pt-0">
          <div className="flex items-center justify-between text-sm">
            <span className="text-[#52688f]">Meta solicitada</span>
            <strong className="text-navy">{targetAmount > 0 ? money.format(targetAmount) : "—"}</strong>
          </div>
          <div className="mt-2 flex items-center justify-between text-sm">
            <span className="text-[#52688f]">Pérdida esperada</span>
            <strong className="text-[#9a5b00]">{summary.invoiceCount ? money.format(summary.expectedLoss) : "—"}</strong>
          </div>
          <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-100">
            <div className="h-full rounded-full bg-[#22b573] transition-[width] duration-500" style={{ width: `${summary.progress}%` }} />
          </div>
          <div className="mt-2 flex items-center justify-between text-xs">
            <span className={targetReached ? "font-semibold text-[#087a4d]" : "text-[#52688f]"}>
              {targetReached ? "Meta cubierta" : targetAmount > 0 ? `Faltan ${money.format(summary.shortfall)}` : "Define una meta"}
            </span>
            <span className="font-semibold text-navy">{Math.round(summary.progress)}%</span>
          </div>
          {hasRecommendation && targetReached && summary.excess > 0 ? <p className="mt-2 text-xs text-[#52688f]">La combinación supera la meta por {money.format(summary.excess)}.</p> : null}
        </div>
      </div>
      <div className="flex gap-3 border-t border-[#e4ebf4] bg-[#f7f9fc] px-5 py-3.5 text-xs leading-5 text-[#52688f] sm:px-6">
        <Icon name="shield" size={17} className="mt-0.5 shrink-0 text-[#38517d]" />
        <p>Esta es una estimación después del costo de factoraje y la pérdida esperada. El monto final dependerá de las ofertas recibidas.</p>
      </div>
    </section>
  );
}

function SelectedInvoices({
  invoices,
  isLoading,
  hasRecommendation,
  onRemove,
}: {
  invoices: Candidate[];
  isLoading: boolean;
  hasRecommendation: boolean;
  onRemove: (invoiceId: number) => void;
}) {
  return (
    <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
      <SectionHeader
        title="Tu paquete recomendado"
        detail={invoices.length ? `${invoices.length} factura${invoices.length === 1 ? "" : "s"} seleccionada${invoices.length === 1 ? "" : "s"}` : "La propuesta aparecerá aquí"}
        badge={invoices.length ? "Editable" : undefined}
      />
      {isLoading ? <LoadingRows /> : invoices.length ? (
        <div className="divide-y divide-slate-100">
          {invoices.map((invoice) => <InvoiceRow key={invoice.id} invoice={invoice} action="remove" onAction={() => onRemove(invoice.id)} />)}
        </div>
      ) : (
        <div className="px-6 py-11 text-center">
          <span className="mx-auto grid size-11 place-items-center rounded-xl bg-[#eff4fa] text-[#52688f]"><Icon name="invoice" size={22} /></span>
          <h3 className="mt-3 text-sm font-semibold text-navy">{hasRecommendation ? "No hay facturas en tu paquete" : "Calcula tu mejor combinación"}</h3>
          <p className="mx-auto mt-1 max-w-md text-sm leading-5 text-[#6b7fa5]">{hasRecommendation ? "Puedes volver a agregarlas desde la lista de disponibles." : "También puedes construir el paquete manualmente agregando facturas disponibles."}</p>
        </div>
      )}
    </section>
  );
}

function AvailableInvoices({ invoices, isLoading, onAdd }: { invoices: Candidate[]; isLoading: boolean; onAdd: (invoiceId: number) => void }) {
  return (
    <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
      <SectionHeader title="Facturas disponibles" detail="Agrégalas para ajustar la propuesta a tus necesidades" />
      {isLoading ? <LoadingRows /> : invoices.length ? (
        <div className="divide-y divide-slate-100">
          {invoices.map((invoice) => <InvoiceRow key={invoice.id} invoice={invoice} action="add" onAction={() => onAdd(invoice.id)} />)}
        </div>
      ) : <p className="px-6 py-9 text-center text-sm text-[#52688f]">Todas las facturas elegibles están dentro del paquete.</p>}
    </section>
  );
}

function SectionHeader({ title, detail, badge }: { title: string; detail: string; badge?: string }) {
  return <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-100 px-5 py-4 sm:px-6"><div><h2 className="text-base font-bold text-navy">{title}</h2><p className="mt-0.5 text-sm text-[#6b7fa5]">{detail}</p></div>{badge ? <span className="rounded-full bg-[#eef9d0] px-2.5 py-1 text-xs font-semibold text-[#426000]">{badge}</span> : null}</div>;
}

function InvoiceRow({ invoice, action, onAction }: { invoice: Candidate; action: "add" | "remove"; onAction: () => void }) {
  return (
    <div className="grid gap-4 px-5 py-4 transition hover:bg-[#fbfcfe] sm:px-6 md:grid-cols-[minmax(130px,1fr)_minmax(108px,.72fr)_minmax(108px,.72fr)_minmax(96px,.6fr)_auto] md:items-center">
      <div className="flex min-w-0 items-center gap-3">
        <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-[#eff4fa] text-navy"><Icon name="invoice" size={18} /></span>
        <div className="min-w-0"><p className="truncate text-sm font-bold text-navy">{invoice.folio}</p><p className="mt-0.5 text-xs text-[#6b7fa5]">Factura elegible</p></div>
      </div>
      <InvoiceValue label="Valor de factura" value={money.format(Number(invoice.amount))} />
      <InvoiceValue label="Estimado a recibir" value={money.format(Number(invoice.net_disbursement))} emphasized />
      <InvoiceValue label="Pérdida esperada" value={money.format(Number(invoice.expected_loss))} warning />
      <button
        type="button"
        onClick={onAction}
        aria-label={`${action === "add" ? "Agregar" : "Retirar"} ${invoice.folio}`}
        className={`inline-flex h-9 items-center justify-center gap-1.5 rounded-lg px-3 text-xs font-semibold outline-none transition focus-visible:ring-2 focus-visible:ring-navy/30 ${action === "add" ? "bg-[#eef9d0] text-[#355400] hover:bg-[#e1f4ad]" : "border border-slate-200 text-[#52688f] hover:border-red-200 hover:bg-red-50 hover:text-red-700"}`}
      >
        <span aria-hidden="true" className="text-base leading-none">{action === "add" ? "+" : "×"}</span>
        {action === "add" ? "Agregar" : "Retirar"}
      </button>
    </div>
  );
}

function InvoiceValue({ label, value, emphasized = false, warning = false }: { label: string; value: string; emphasized?: boolean; warning?: boolean }) {
  return <div><p className="text-[11px] font-medium text-[#7a8cab]">{label}</p><p className={`mt-0.5 text-sm ${emphasized ? "font-bold text-navy" : warning ? "font-semibold text-[#9a5b00]" : "font-semibold text-[#38517d]"}`}>{value}</p></div>;
}

function PublishSummary({ term, targetAmount, summary, isPublishing, onPublish }: { term: number; targetAmount: number; summary: ReturnType<typeof summarizePackage>; isPublishing: boolean; onPublish: () => void }) {
  return (
    <aside className="rounded-2xl bg-navy px-5 py-5 text-white shadow-[0_14px_32px_rgba(11,31,68,.14)] xl:sticky xl:top-5">
      <div className="flex items-center justify-between"><h2 className="text-base font-bold">Resumen del paquete</h2><span className="rounded-full bg-white/10 px-2.5 py-1 text-xs font-semibold text-[#dce5f3]">{term} días</span></div>
      <dl className="mt-5 space-y-3 text-sm">
        <SummaryLine label="Efectivo estimado" value={money.format(summary.estimatedCash)} strong />
        <SummaryLine label="Pérdida esperada" value={money.format(summary.expectedLoss)} />
        <SummaryLine label="Valor de facturas" value={money.format(summary.nominalAmount)} />
        <SummaryLine label="Facturas" value={String(summary.invoiceCount)} />
      </dl>
      <div className="my-5 h-px bg-white/12" />
      <div className="flex items-center justify-between text-xs"><span className="text-[#b8c7e1]">Cobertura de la meta</span><strong>{targetAmount > 0 ? `${Math.round(summary.progress)}%` : "—"}</strong></div>
      <button
        type="button"
        disabled={!summary.invoiceCount || isPublishing}
        onClick={onPublish}
        className="mt-4 inline-flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-lime text-sm font-bold text-navy outline-none transition hover:bg-[#e0f88a] focus-visible:ring-2 focus-visible:ring-white disabled:cursor-not-allowed disabled:bg-[#52688f] disabled:text-[#c5d0e1]"
      >
        <Icon name={isPublishing ? "clock" : "arrow"} size={18} />
        {isPublishing ? "Publicando..." : "Publicar paquete"}
      </button>
      <p className="mt-3 text-center text-[11px] leading-4 text-[#aebdd5]">Publicar no garantiza el monto final. Recibirás ofertas de las financiadoras.</p>
    </aside>
  );
}

function SummaryLine({ label, value, strong = false }: { label: string; value: string; strong?: boolean }) {
  return <div className={`flex items-end justify-between gap-3 ${strong ? "pb-3" : ""}`}><dt className="text-[#b8c7e1]">{label}</dt><dd className={strong ? "text-xl font-bold tracking-[-.02em]" : "font-semibold"}>{value}</dd></div>;
}

function LoadingRows() {
  return <div className="space-y-3 px-6 py-5" aria-label="Cargando facturas"><div className="h-12 animate-pulse rounded-lg bg-slate-100" /><div className="h-12 animate-pulse rounded-lg bg-slate-100" /><div className="h-12 animate-pulse rounded-lg bg-slate-100" /></div>;
}

function parseMoneyInput(value: string): number {
  const normalized = value.replace(/[^0-9.]/g, "");
  const parsed = Number(normalized);
  return Number.isFinite(parsed) ? parsed : 0;
}
