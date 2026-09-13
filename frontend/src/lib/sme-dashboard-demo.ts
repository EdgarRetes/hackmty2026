export interface LiquidityDemoPoint {
  label: string;
  withFactora: number;
  withoutFinancing: number;
}

// Temporary visualization factors. Replace this module when the backend exposes
// projected cash-flow scenarios. Amounts are scaled from live Dashboard KPIs so
// the demo remains visually consistent with the current company data.
const MONTHS = ["Sep", "Oct", "Nov", "Dic", "Ene", "Feb"] as const;
const WITH_FACTORA = [0.82, 1.04, 1.27, 1.42, 1.68, 1.9] as const;
const WITHOUT_FINANCING = [0.64, 0.78, 0.74, 0.7, 0.83, 0.96] as const;

export function buildLiquidityDemo(values: { receivablesAmount: number; eligibleAmount: number; financedAmount: number }): LiquidityDemoPoint[] {
  const base = Math.max(values.receivablesAmount, values.eligibleAmount + values.financedAmount, 1);
  return MONTHS.map((label, index) => ({
    label,
    withFactora: base * WITH_FACTORA[index],
    withoutFinancing: base * WITHOUT_FINANCING[index],
  }));
}
