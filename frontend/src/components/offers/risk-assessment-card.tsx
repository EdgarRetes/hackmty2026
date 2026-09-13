import type { RiskAssessment } from "./data";

const decisionStyle = {
  APPROVE: { label: "Aprobada", badge: "bg-[#e8f6b8] text-[#314000]", panel: "bg-[#f7fbe9]" },
  REVIEW: { label: "Revisión manual", badge: "bg-[#fff0cf] text-[#7a4300]", panel: "bg-[#fffaf0]" },
  REJECT: { label: "No elegible", badge: "bg-[#fee7e7] text-[#9b1c1c]", panel: "bg-[#fff7f7]" },
} as const;

export function RiskAssessmentCard({ assessment }: { assessment: RiskAssessment }) {
  const style = decisionStyle[assessment.decision];
  const metrics = [
    ["Probabilidad de incumplimiento", assessment.probabilityOfDefault],
    ["Pérdida dado incumplimiento", assessment.lossGivenDefault],
    ["Pérdida esperada", assessment.expectedLoss],
    ["Tasa mensual sugerida", assessment.monthlyRate],
    ["Plazo restante", `${assessment.termDays} días`],
    ["Utilidad esperada", assessment.expectedProfit],
  ];

  return <section aria-labelledby="risk-heading" className={`mt-5 rounded-xl px-5 py-5 ${style.panel}`}>
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div>
        <p className="text-xs font-semibold text-[#52688f]">Evaluación para inversionista</p>
        <div className="mt-1.5 flex flex-wrap items-center gap-2.5">
          <h2 id="risk-heading" className="text-xl font-bold text-navy">Riesgo {assessment.rating === "N" ? "sin calificar" : `nivel ${assessment.rating}`}</h2>
          <span className={`rounded-lg px-2.5 py-1 text-xs font-semibold ${style.badge}`}>{style.label}</span>
        </div>
        <p className="mt-1 text-sm text-[#52688f]">Puntaje {assessment.score}/100 · Confianza {confidenceLabel(assessment.confidence)}</p>
      </div>
      <div className="text-left sm:text-right">
        <p className="text-xs text-[#52688f]">Política {assessment.policyVersion}</p>
        <a className="mt-1 inline-block text-xs font-medium text-blue-600 underline decoration-blue-200 underline-offset-2 focus:outline-none focus:ring-2 focus:ring-blue-400" href={assessment.referenceRateSource} target="_blank" rel="noreferrer">TIIE validada al {assessment.referenceRateAsOf}</a>
      </div>
    </div>

    <dl className="mt-5 grid gap-x-6 gap-y-4 border-t border-slate-200/80 pt-4 sm:grid-cols-2 lg:grid-cols-3">
      {metrics.map(([label, value]) => <div key={label}><dt className="text-xs text-[#52688f]">{label}</dt><dd className="mt-0.5 text-base font-bold text-navy">{value}</dd></div>)}
    </dl>

    <div className="mt-5 grid gap-4 border-t border-slate-200/80 pt-4 lg:grid-cols-[1fr_auto]">
      <div><h3 className="text-sm font-semibold text-navy">Por qué obtuvimos este resultado</h3><ul className="mt-2 space-y-1.5 text-sm leading-5 text-[#38517d]">{assessment.reasons.map((reason) => <li key={reason} className="flex gap-2"><span aria-hidden="true" className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-[#8eb51c]"/>{reason}</li>)}</ul></div>
      {assessment.warnings.length > 0 && <aside className="max-w-md rounded-lg bg-white/80 px-4 py-3"><h3 className="text-sm font-semibold text-[#7a4300]">Consideraciones</h3><ul className="mt-1.5 space-y-1 text-xs leading-5 text-[#704f27]">{assessment.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul></aside>}
    </div>
  </section>;
}

function confidenceLabel(value: string) {
  return ({ high: "alta", medium: "media", low: "baja" } as Record<string, string>)[value] ?? value;
}
