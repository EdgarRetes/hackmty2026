import assert from "node:assert/strict";
import test from "node:test";

import { summarizePackage } from "./package-builder-state.ts";

const candidates = [
  { id: 1, amount: "110000.00", net_disbursement: "95000.00", expected_loss: "8000.00" },
  { id: 2, amount: "115000.00", net_disbursement: "105000.00", expected_loss: "2000.00" },
];

test("summarizes the visible selection against the liquidity target", () => {
  assert.deepEqual(summarizePackage(candidates, [2], 100000), {
    invoiceCount: 1,
    nominalAmount: 115000,
    estimatedCash: 105000,
    expectedLoss: 2000,
    progress: 100,
    shortfall: 0,
    excess: 5000,
  });
});

test("reports the remaining shortfall without a target overshoot", () => {
  assert.deepEqual(summarizePackage(candidates, [1], 100000), {
    invoiceCount: 1,
    nominalAmount: 110000,
    estimatedCash: 95000,
    expectedLoss: 8000,
    progress: 95,
    shortfall: 5000,
    excess: 0,
  });
});
