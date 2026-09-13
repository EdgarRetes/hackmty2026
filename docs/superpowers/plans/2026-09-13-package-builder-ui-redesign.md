# Package Builder UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn `/invoices/package` into a liquidity-first, editable package workspace that matches Factora's existing fintech UI.

**Architecture:** Keep the existing API contract and move selection totals into a small tested utility. Rebuild `PackageBuilder` as an Operate-mode workspace with a dominant liquidity configurator, financial summary, selected invoice list, available invoice list, and sticky publication summary.

**Tech Stack:** Next.js 16 App Router, React 19, TypeScript, Tailwind CSS 4, Node test runner.

## Global Constraints

- Liquidity target is the primary mode.
- Manual editing uses explicit add and remove actions; drag and drop is optional enhancement only.
- Use `Estimado a recibir`, not repeated `netos` labels.
- State clearly that calculations are estimates and final cash depends on offers.
- Reuse navy, lime, neutral backgrounds, existing iconography, borders, and restrained shadows.
- Do not add dependencies or change the backend API.

---

### Task 1: Tested package selection calculations

**Files:**
- Create: `frontend/src/components/invoices/package-builder-state.ts`
- Create: `frontend/src/components/invoices/package-builder-state.test.ts`
- Modify: `frontend/src/components/invoices/package-builder.tsx`

**Interfaces:**
- Consumes: preview candidates with `id`, `amount`, `net_disbursement`, and `expected_loss` decimal strings.
- Produces: `summarizePackage(candidates, selectedIds, target)` returning invoice count, nominal amount, estimated cash, expected loss, progress percentage, shortfall, and excess.

- [ ] **Step 1: Write the failing test**

```ts
test("summarizes the visible selection against the liquidity target", () => {
  assert.deepEqual(summarizePackage(candidates, [2], 100_000), {
    invoiceCount: 1,
    nominalAmount: 115_000,
    estimatedCash: 105_000,
    expectedLoss: 2_000,
    progress: 100,
    shortfall: 0,
    excess: 5_000,
  });
});
```

- [ ] **Step 2: Verify RED**

Run: `node --experimental-strip-types --test src/components/invoices/package-builder-state.test.ts`

Expected: FAIL because `package-builder-state.ts` does not exist.

- [ ] **Step 3: Implement the calculation utility**

```ts
export function summarizePackage(candidates, selectedIds, target) {
  const selected = candidates.filter((candidate) => selectedIds.includes(candidate.id));
  const estimatedCash = selected.reduce((sum, item) => sum + Number(item.net_disbursement), 0);
  return {
    invoiceCount: selected.length,
    nominalAmount: selected.reduce((sum, item) => sum + Number(item.amount), 0),
    estimatedCash,
    expectedLoss: selected.reduce((sum, item) => sum + Number(item.expected_loss), 0),
    progress: target > 0 ? Math.min(100, (estimatedCash / target) * 100) : 0,
    shortfall: Math.max(0, target - estimatedCash),
    excess: Math.max(0, estimatedCash - target),
  };
}
```

- [ ] **Step 4: Verify GREEN**

Run: `node --experimental-strip-types --test src/components/invoices/package-builder-state.test.ts`

Expected: PASS.

### Task 2: Liquidity-first workspace UI

**Files:**
- Modify: `frontend/src/components/invoices/package-builder.tsx`

**Interfaces:**
- Consumes: `previewPackage`, `createPublication`, `summarizePackage`, and existing `Icon` components.
- Produces: configurable, editable and responsive package builder at `/invoices/package`.

- [ ] **Step 1: Establish a failing compilation boundary**

Reference focused subcomponents `LiquidityConfigurator`, `PackageSummary`, `SelectedInvoices`, and `AvailableInvoices` from `PackageBuilder` before defining them.

- [ ] **Step 2: Verify RED**

Run: `npm run lint`

Expected: FAIL with undefined component identifiers.

- [ ] **Step 3: Implement the redesigned workspace**

Implement the approved hierarchy, explicit add/remove actions, loading and error states, target coverage feedback, sticky publish panel, accessible labels, responsive cards, and honest estimation copy. Preserve request payloads and navigation behavior.

- [ ] **Step 4: Verify behavior and production output**

Run: `node --experimental-strip-types --test src/components/invoices/package-builder-state.test.ts && npm run lint && $env:NEXT_PUBLIC_API_URL='http://127.0.0.1:8000'; npm run build`

Expected: test PASS, lint PASS, build PASS.

- [ ] **Step 5: Perform bounded visual QA**

Inspect `/invoices/package` once at desktop and mobile widths, fix all observed hierarchy, overflow, focus, loading, and copy defects in one batch, then perform one confirmation pass.

- [ ] **Step 6: Run the design detector and commit**

Run: `node C:\Users\a2005\.codex\skills\impeccable\scripts\detect.mjs --json frontend/src/components/invoices/package-builder.tsx frontend/src/components/invoices/package-builder-state.ts`

Expected: no blocking findings.

Commit: `git commit -m "feat: redesign package builder experience"`.
