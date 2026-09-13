# Package Factoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let an SME compose and publish a 30/60/90-day invoice package manually or from a liquidity-target recommendation based on net cash and expected loss.

**Architecture:** Add a term-aware evaluator and sparse 0/1 knapsack service in `facturas`, expose a preview endpoint, extend batch publication with a persisted term, and provide an editable Next.js builder.

**Tech Stack:** Django, DRF, Python `Decimal`, Next.js, React, TypeScript, Tailwind CSS.

## Global Constraints

- API is JSON and money remains decimal strings.
- Valid terms are exactly 30, 60, and 90 days.
- Candidates are pending, unbatched, same-company and `APPROVE` at the chosen term.
- Do not add dependencies.
- Apply TDD: observe each new test fail before implementation.

---

### Task 1: Term-aware evaluation and batch persistence

**Files:**
- Modify: `backend/core/risk_engine.py`
- Modify: `backend/facturas/models.py`
- Create: `backend/facturas/migrations/0004_invoicebatch_factoring_term_days.py`
- Modify: `backend/facturas/tests.py`

**Interfaces:** Produces `evaluate_invoice(invoice, as_of=None, term_days=None)` and `InvoiceBatch.factoring_term_days`.

- [ ] **Step 1: Write the failing test**

```python
def test_evaluation_uses_explicit_factoring_term_for_pricing(self):
    thirty = evaluate_invoice(self.invoice, term_days=30)
    ninety = evaluate_invoice(self.invoice, term_days=90)
    self.assertEqual(thirty["term_days"], 30)
    self.assertGreater(ninety["financing_cost"], thirty["financing_cost"])
    self.assertLess(ninety["net_disbursement"], thirty["net_disbursement"])
```

- [ ] **Step 2: Run it to verify RED**

Run: `python manage.py test facturas.tests -v 2`.

Expected: FAIL because `term_days` is not accepted.

- [ ] **Step 3: Write minimal implementation**

Add the optional term override to scoring and pricing while retaining due-date behavior when omitted. Add the model field, allow only `(30, 60, 90)`, and generate the migration.

- [ ] **Step 4: Run it to verify GREEN**

Run: `python manage.py test facturas.tests -v 2`.

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add backend/core/risk_engine.py backend/facturas/models.py backend/facturas/migrations/0004_invoicebatch_factoring_term_days.py backend/facturas/tests.py; git commit -m "feat: make package pricing term-aware"`.

### Task 2: Optimizer and preview API

**Files:**
- Create: `backend/facturas/package_optimizer.py`
- Modify: `backend/facturas/views.py`
- Modify: `backend/facturas/urls.py`
- Modify: `backend/facturas/serializers.py`
- Modify: `backend/facturas/tests.py`
- Modify: `backend/API_CONTRACT.md`

**Interfaces:** Produces `recommend_package(candidates, liquidity_target)` and `POST /api/invoice-batches/preview/`.

- [ ] **Step 1: Write failing tests**

```python
def test_recommendation_reaches_target_with_net_cash_and_lowest_loss(self):
    recommendation = recommend_package(candidates, Decimal("100000.00"))
    self.assertTrue(recommendation.target_reached)
    self.assertEqual(recommendation.invoice_ids, [self.low_loss_invoice.id])

def test_preview_rejects_invalid_term(self):
    response = self.client.post("/api/invoice-batches/preview/", {"term_days": 45, "mode": "manual"}, format="json")
    self.assertEqual(response.status_code, 400)
```

- [ ] **Step 2: Run tests to verify RED**

Run: `python manage.py test facturas.tests -v 2`.

Expected: FAIL because the optimizer and preview route are absent.

- [ ] **Step 3: Write minimal implementation**

Implement a sparse 0/1 state frontier. A state contains invoice ids, net cash, expected loss and nominal amount. Prune dominated states. Select sufficient states by minimum loss, then smallest excess, then fewest invoices; otherwise choose maximum net cash with the same tie-breaks. Evaluate candidates at the requested term and retain only `APPROVE` invoices.

- [ ] **Step 4: Run tests to verify GREEN**

Run: `python manage.py test facturas.tests -v 2`.

Expected: PASS.

- [ ] **Step 5: Update contract and commit**

Run: `git add backend/facturas/package_optimizer.py backend/facturas/views.py backend/facturas/urls.py backend/facturas/serializers.py backend/facturas/tests.py backend/API_CONTRACT.md; git commit -m "feat: preview optimized invoice packages"`.

### Task 3: Term-aware publication

**Files:**
- Modify: `backend/facturas/views.py`
- Modify: `backend/facturas/serializers.py`
- Modify: `backend/facturas/tests.py`
- Modify: `backend/API_CONTRACT.md`

**Interfaces:** Consumes `{ "invoice_ids": [87, 97], "term_days": 60 }`; produces a batch including `factoring_term_days`.

- [ ] **Step 1: Write failing test**

```python
def test_publishes_approved_selection_with_selected_term(self):
    response = self.client.post("/api/invoice-batches/", {"invoice_ids": [self.invoice.id], "term_days": 60}, format="json")
    self.assertEqual(response.status_code, 201)
    self.assertEqual(response.data["factoring_term_days"], 60)
```

- [ ] **Step 2: Run test to verify RED**

Run: `python manage.py test facturas.tests -v 2`.

Expected: FAIL because the endpoint ignores `term_days`.

- [ ] **Step 3: Write minimal implementation**

Validate the term and the re-evaluated `APPROVE` decision of every invoice before creating the batch. Serialize the persisted term and update the API contract.

- [ ] **Step 4: Run test to verify GREEN**

Run: `python manage.py test facturas.tests -v 2`.

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add backend/facturas/views.py backend/facturas/serializers.py backend/facturas/tests.py backend/API_CONTRACT.md; git commit -m "feat: publish invoice packages with term"`.

### Task 4: Frontend builder

**Files:**
- Create: `frontend/src/app/invoices/package/page.tsx`
- Create: `frontend/src/components/invoices/package-builder.tsx`
- Modify: `frontend/src/components/invoices/invoices-page.tsx`
- Modify: `frontend/src/lib/publications.ts`

**Interfaces:** Consumes preview API and `createPublication(invoiceIds, termDays)`; produces `/invoices/package`.

- [ ] **Step 1: Write failing interface verification**

Reference `previewPackage` from the new route before it exists.

- [ ] **Step 2: Run it to verify RED**

Run: `npm run lint`.

Expected: FAIL with unresolved `previewPackage`.

- [ ] **Step 3: Write minimal implementation**

Add typed preview and term-aware publication clients. Build Spanish UI for term selection, manual/liquidity mode, target input, candidate checkboxes, live totals, editable recommended selection, and publication. Add `Crear paquete` as the invoice-page upper-right action.

- [ ] **Step 4: Run it to verify GREEN**

Run: `npm run lint && npm run build`.

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add frontend/src/app/invoices/package/page.tsx frontend/src/components/invoices/package-builder.tsx frontend/src/components/invoices/invoices-page.tsx frontend/src/lib/publications.ts; git commit -m "feat: add invoice package builder"`.

### Task 5: Validation and push

**Files:** No source changes unless validation reveals a defect.

- [ ] **Step 1: Run backend validation**

Run: `python manage.py makemigrations --check && python manage.py test -v 2`.

Expected: PASS.

- [ ] **Step 2: Run frontend validation**

Run: `npm run lint && npm run build`.

Expected: PASS.

- [ ] **Step 3: Inspect final state**

Run: `git diff --check && git status --short`.

Expected: no whitespace errors and no uncommitted feature files.

- [ ] **Step 4: Push after all checks pass**

Run: `git push`.

Expected: remote accepts all commits.
