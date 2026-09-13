export interface PackageCandidateAmounts {
  id: number;
  amount: string;
  net_disbursement: string;
  expected_loss: string;
}

export interface PackageSummary {
  invoiceCount: number;
  nominalAmount: number;
  estimatedCash: number;
  expectedLoss: number;
  progress: number;
  shortfall: number;
  excess: number;
}

export function summarizePackage(
  candidates: PackageCandidateAmounts[],
  selectedIds: number[],
  target: number,
): PackageSummary {
  const selected = candidates.filter((candidate) => selectedIds.includes(candidate.id));
  const estimatedCash = selected.reduce(
    (sum, candidate) => sum + Number(candidate.net_disbursement),
    0,
  );

  return {
    invoiceCount: selected.length,
    nominalAmount: selected.reduce((sum, candidate) => sum + Number(candidate.amount), 0),
    estimatedCash,
    expectedLoss: selected.reduce((sum, candidate) => sum + Number(candidate.expected_loss), 0),
    progress: target > 0 ? Math.min(100, (estimatedCash / target) * 100) : 0,
    shortfall: Math.max(0, target - estimatedCash),
    excess: Math.max(0, estimatedCash - target),
  };
}
