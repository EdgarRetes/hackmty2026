"""
Payment-delay risk engine: predicts a p10/p50/p90 "days late" band for a
pending Invoice, based on that invoice's DebtorClient's payment history.

Trains three separate GradientBoostingRegressor models (loss="quantile",
alpha=0.1/0.5/0.9) on PaymentHistory rows pooled across every client.
Features per row:
  - archetype (one-hot: reliable / irregular / delinquent / new)
  - amount_ratio: that payment's amount relative to the client's own
    historical average amount
  - days_since_last_payment: gap since that client's previous payment

Honesty check: with a few dozen synthetic PaymentHistory rows total, this
is a demo-scale model, not a statistically robust one — it's here to
prove the pipeline (features -> quantile model -> a band a lender could
act on), not to be trusted at hackathon-judged precision. Swap in real
payment data and this should get meaningfully better without changing
the interface.
"""

import statistics
from collections import defaultdict

import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor

from empresas.models import PaymentHistory

ARCHETYPES = ("reliable", "irregular", "delinquent", "new")
FEATURE_COLUMNS = [f"archetype_{a}" for a in ARCHETYPES] + [
    "amount_ratio",
    "days_since_last_payment",
]
QUANTILES = (0.1, 0.5, 0.9)

# Used when a client has no prior payment to measure recency from (a
# brand-new client, or the very first payment in a training row).
DEFAULT_DAYS_SINCE_LAST_PAYMENT = 45

_cache = {}


def _archetype_one_hot(archetype):
    return {f"archetype_{a}": 1.0 if a == archetype else 0.0 for a in ARCHETYPES}


def _build_training_frame():
    records = list(
        PaymentHistory.objects.select_related("debtor_client").order_by(
            "debtor_client_id", "paid_at"
        )
    )

    amounts_by_client = defaultdict(list)
    for record in records:
        amounts_by_client[record.debtor_client_id].append(float(record.amount))
    avg_amount_by_client = {
        client_id: statistics.mean(amounts)
        for client_id, amounts in amounts_by_client.items()
    }

    rows = []
    last_paid_at_by_client = {}
    for record in records:
        client_id = record.debtor_client_id
        avg_amount = avg_amount_by_client[client_id]

        previous_paid_at = last_paid_at_by_client.get(client_id)
        if previous_paid_at is not None:
            days_since_last_payment = (record.paid_at - previous_paid_at).days
        else:
            days_since_last_payment = DEFAULT_DAYS_SINCE_LAST_PAYMENT
        last_paid_at_by_client[client_id] = record.paid_at

        row = _archetype_one_hot(record.debtor_client.archetype)
        row["amount_ratio"] = float(record.amount) / avg_amount if avg_amount else 1.0
        row["days_since_last_payment"] = days_since_last_payment
        row["days_late"] = record.days_late
        rows.append(row)

    return pd.DataFrame(rows, columns=FEATURE_COLUMNS + ["days_late"])


def train_models():
    """Fits and returns {quantile: fitted GradientBoostingRegressor}."""
    df = _build_training_frame()
    if df.empty:
        raise RuntimeError(
            "No PaymentHistory records found — run "
            "`python manage.py seed_demo_data` first."
        )

    X = df[FEATURE_COLUMNS]
    y = df["days_late"]
    # Small dataset: shallow, few trees, and a leaf-size floor that scales
    # with the data, to avoid each tree memorizing individual rows.
    min_samples_leaf = max(3, len(df) // 10)

    models = {}
    for quantile in QUANTILES:
        model = GradientBoostingRegressor(
            loss="quantile",
            alpha=quantile,
            n_estimators=50,
            max_depth=2,
            min_samples_leaf=min_samples_leaf,
            random_state=42,
        )
        model.fit(X, y)
        models[quantile] = model
    return models


def _get_models():
    if "models" not in _cache:
        _cache["models"] = train_models()
    return _cache["models"]


def predict_risk(invoice):
    """
    Returns {"p10": int, "p50": int, "p90": int} — predicted days-late
    band for the given Invoice (an Invoice instance; doesn't need to be
    saved to the database).
    """
    models = _get_models()
    client = invoice.debtor_client
    history = list(client.payment_history.order_by("paid_at"))

    if history:
        avg_amount = statistics.mean(float(h.amount) for h in history)
        days_since_last_payment = max(0, (invoice.issue_date - history[-1].paid_at).days)
    else:
        # No history at all (a brand-new client): nothing to compare the
        # amount against, so amount_ratio falls back to a neutral 1.0.
        avg_amount = float(invoice.amount)
        days_since_last_payment = DEFAULT_DAYS_SINCE_LAST_PAYMENT

    amount_ratio = float(invoice.amount) / avg_amount if avg_amount else 1.0

    row = _archetype_one_hot(client.archetype)
    row["amount_ratio"] = amount_ratio
    row["days_since_last_payment"] = days_since_last_payment
    X = pd.DataFrame([row], columns=FEATURE_COLUMNS)

    predictions = {q: float(models[q].predict(X)[0]) for q in QUANTILES}
    # Separately-trained quantile models can "cross" (e.g. p10 > p50) on
    # small data — sorting is the standard fix.
    p10, p50, p90 = sorted(predictions[q] for q in QUANTILES)

    return {"p10": round(p10), "p50": round(p50), "p90": round(p90)}
