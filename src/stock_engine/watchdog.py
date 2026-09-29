"""Educational surveillance of actual matching-engine executions, not fraud detection."""
from __future__ import annotations

import random
import time
from uuid import uuid4

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .session import ExchangeSession

BASELINE = 40
FEATURES = ("quantity", "price_change_pct", "execution_count", "submitted_quantity",
            "bid_depth", "ask_depth", "depth_imbalance")
NOTE = ("Needs review does not mean fraud. The first 40 executed-order observations form a fixed "
        "baseline; only later observations are scored. Depth covers the top 30 price levels. "
        "No order is blocked and no future price is predicted.")


def report(session: ExchangeSession, symbol: str = "ACME") -> dict:
    rows = [row for row in session.observations if row["symbol"] == symbol.upper()]
    output = {"symbol": symbol.upper(), "observations": len(rows), "baseline_size": BASELINE,
              "status": "warming_up", "alerts": [], "timeline": [], "flagged": 0,
              "features": list(FEATURES), "note": NOTE, "source": "Actual simulated engine executions"}
    if len(rows) <= BASELINE:
        return output
    matrix = np.array([[row[name] for name in FEATURES] for row in rows], dtype=float)
    baseline, heldout = matrix[:BASELINE], matrix[BASELINE:]
    model = make_pipeline(StandardScaler(), IsolationForest(n_estimators=150, contamination=0.05, random_state=42))
    model.fit(baseline)
    decisions = model.decision_function(heldout)
    z = np.abs(model[0].transform(heldout))
    timeline = []
    for index, (row, decision) in enumerate(zip(rows[BASELINE:], decisions)):
        names = [FEATURES[j] for j in np.argsort(z[index])[::-1][:3]]
        unusual = bool(decision < 0)
        timeline.append({**row, "needs_review": unusual,
                         "score": round(float(np.clip(0.5 - 2 * decision, 0, 1)), 4),
                         "reasons": names, "message": "Unusual execution; review suggested" if unusual else "Within baseline pattern"})
    output.update(status="monitoring", timeline=timeline[-200:],
                  alerts=[row for row in timeline if row["needs_review"]][-100:],
                  flagged=sum(row["needs_review"] for row in timeline), scored=len(timeline))
    return output


def classroom_demo(seed: int = 42) -> tuple[ExchangeSession, dict]:
    """Train on normal executions, then evaluate unseen normal + injected events.

    Labels are withheld from the model. This is synthetic evaluation, not a
    claim about performance on real market manipulation.
    """
    session, rng = ExchangeSession(), random.Random(seed)
    labels = []
    for cycle in range(90):
        injected = 60 <= cycle < 70
        price = f"{130 + rng.randrange(-2, 3) if injected else 100 + rng.randrange(-2, 3) / 10:.2f}"
        quantity = rng.randrange(2000, 5000) if injected else rng.randrange(20, 61)
        session.place_order(f"DEMO-S{cycle}", "ACME", "SELL", quantity, price)
        session.place_order(f"DEMO-B{cycle}", "ACME", "BUY", quantity, price)
        if cycle >= BASELINE:
            labels.append(injected)
    result = report(session)
    predictions = [row["needs_review"] for row in result["timeline"]]
    tp = sum(expected and predicted for expected, predicted in zip(labels, predictions))
    fp = sum(not expected and predicted for expected, predicted in zip(labels, predictions))
    fn = sum(expected and not predicted for expected, predicted in zip(labels, predictions))
    tn = sum(not expected and not predicted for expected, predicted in zip(labels, predictions))
    evaluation = {"seed": seed, "training": BASELINE, "heldout": len(labels),
                  "true_positives": tp, "false_positives": fp, "false_negatives": fn, "true_negatives": tn,
                  "precision": tp / (tp + fp) if tp + fp else 0,
                  "recall": tp / (tp + fn) if tp + fn else 0,
                  "note": "Synthetic holdout only. Price transitions back to normal can also trigger alerts."}
    return session, {"watchdog": result, "evaluation": evaluation,
                     "steps": ["40 normal executions establish the baseline", "20 unseen normal executions",
                               "10 injected volume/price spikes", "20 normal executions resume"]}


def simulate(session: ExchangeSession, count: int, scenario: str, symbol: str, seed: int,
             buy_probability: int, market_percent: int) -> dict:
    rng, prefix = random.Random(seed), uuid4().hex[:10]
    before = len(session.engine.trades())
    filled = 0
    started = time.perf_counter()
    for index in range(count):
        drift = index / count * (8 if scenario == "bull" else -8 if scenario == "bear" else 0)
        width = 10 if scenario == "volatile" else 2
        price = f"{100 + drift + rng.uniform(-width, width):.2f}"
        quantity = rng.randrange(1, 11) if scenario == "low_liquidity" else rng.randrange(100, 501) if scenario == "high_liquidity" else rng.randrange(10, 101)
        result = session.place_order(f"SIM-{prefix}-{index}", symbol, "BUY" if rng.randrange(100) < buy_probability else "SELL",
                                     quantity, None if rng.randrange(100) < market_percent else price)
        filled += result.filled
    elapsed = time.perf_counter() - started
    return {"commands": count, "filled_shares": filled, "trades": len(session.engine.trades()) - before,
            "seconds": elapsed, "commands_per_second": count / elapsed, "seed": seed,
            "scenario": scenario, "symbol": symbol, "note": "Measured session processing, including telemetry; not an isolated engine benchmark."}
