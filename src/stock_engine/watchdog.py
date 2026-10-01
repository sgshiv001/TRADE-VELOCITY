"""Advisory anomaly monitoring of matching-engine executions."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
from threading import RLock
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .session import ExchangeSession

BASELINE = 40
FIT_SIZE = 24
MODEL_VERSION = "execution-watchdog-v3"
FEATURES = ("quantity", "price_change_pct", "execution_count", "submitted_quantity",
            "bid_depth", "ask_depth", "depth_imbalance")
LOG_COLUMNS = (0, 2, 3, 4, 5)
# Minimum meaningful variability, in transformed feature units. In particular,
# constant features must not cause division by zero or flag every tiny change.
SCALE_FLOORS = np.array([.25, .25, .25, .25, .75, .75, .10])
NOTE = ("Needs review does not mean fraud. The first 40 executed-order observations form a fixed "
        "baseline: 24 fit the detector and 16 calibrate its cutoffs. Only later observations are "
        "scored. Isolation Forest is combined with explicit robust-deviation guards. Calibration "
        "assumes the baseline is representative; controlled-test results are not real-market fraud "
        "accuracy. Depth covers the top 30 price levels. No order is blocked or price predicted.")


@dataclass(frozen=True)
class Settings:
    forest_margin: float = .08
    guard_floor: float = 8.0
    guard_padding: float = 1.0
    forest_confirmation: float = 4.0
    size_multiplier: float = 20.0

    def __post_init__(self):
        if not (0 <= self.forest_margin <= .25 and 3 <= self.guard_floor <= 20 and .1 <= self.guard_padding <= 5
                and 0 <= self.forest_confirmation <= 5 and 5 <= self.size_multiplier <= 100):
            raise ValueError("invalid watchdog calibration settings")


def default_settings() -> Settings:
    path = Path(__file__).parent / "data" / "watchdog-calibration.json"
    if not path.exists():
        return Settings()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("model_version") != MODEL_VERSION:
        raise ValueError("unsupported watchdog calibration version")
    return Settings(**{name: payload[name] for name in Settings.__dataclass_fields__})


def transform(matrix: np.ndarray) -> np.ndarray:
    values = np.array(matrix, dtype=float, copy=True)
    if not np.isfinite(values).all():
        raise ValueError("execution monitor features must be finite")
    values[:, LOG_COLUMNS] = np.log1p(np.maximum(0, values[:, LOG_COLUMNS]))
    return values


class CalibratedBaseline:
    """Fit on a prefix; reserve distinct normal observations for cutoff fitting."""

    def __init__(self, baseline: np.ndarray):
        values = transform(baseline)
        fit, calibration = values[:FIT_SIZE], values[FIT_SIZE:BASELINE]
        if len(fit) != FIT_SIZE or len(calibration) != BASELINE - FIT_SIZE:
            raise ValueError("40 observations are required to calibrate the execution monitor")
        self.model = make_pipeline(StandardScaler(), IsolationForest(n_estimators=150, contamination="auto", random_state=42))
        self.model.fit(fit)
        self.center = np.median(fit, axis=0)
        mad = 1.4826 * np.median(np.abs(fit - self.center), axis=0)
        self.scale = np.maximum(mad, SCALE_FLOORS)
        self.calibration_forest_max = float((-self.model.score_samples(calibration)).max())
        self.calibration_guard_max = float((np.abs(calibration - self.center) / self.scale).max())
        self.varying_features = int((np.ptp(fit, axis=0) > 1e-9).sum())
        # A raw-count envelope supplements log/MAD guards for highly variable
        # baselines. Cutoff observations may enlarge this fixed envelope.
        self.count_envelope = np.maximum(0, np.asarray(baseline)[:, LOG_COLUMNS]).max(axis=0) + 1

    def count_ratios(self, matrix: np.ndarray):
        return (np.maximum(0, np.asarray(matrix)[:, LOG_COLUMNS]) + 1) / self.count_envelope

    def components(self, matrix: np.ndarray):
        values = transform(matrix)
        forest = -self.model.score_samples(values)
        deviations = np.abs(values - self.center) / self.scale
        return forest, deviations

    def thresholds(self, settings: Settings):
        return (self.calibration_forest_max + settings.forest_margin,
                max(settings.guard_floor, self.calibration_guard_max + settings.guard_padding))

    def score(self, matrix: np.ndarray, settings: Settings):
        forest, deviations = self.components(matrix)
        forest_threshold, guard_threshold = self.thresholds(settings)
        forest_flags = (forest > forest_threshold) & (deviations.max(axis=1) > settings.forest_confirmation)
        guard_flags = deviations.max(axis=1) > guard_threshold
        ratios = self.count_ratios(matrix)
        envelope_flags = ratios.max(axis=1) > settings.size_multiplier
        # Display severity relative to fixed cutoffs, NOT a probability or a
        # batch-normalized score. Later observations cannot change old scores.
        severity = np.clip(np.maximum.reduce([
            np.minimum(.5 + 2 * (forest - forest_threshold),
                       .5 * deviations.max(axis=1) / max(settings.forest_confirmation, .1)),
            .5 * deviations.max(axis=1) / guard_threshold,
            .5 * ratios.max(axis=1) / settings.size_multiplier]), 0, 1)
        return forest_flags, guard_flags, envelope_flags, severity, deviations, forest, ratios


class ExecutionMonitor:
    """Reuse fixed baseline models and unchanged reports, away from the book lock."""

    def __init__(self, settings: Settings | None = None):
        self.lock = RLock()
        self.models = {}
        self.cache = {}
        self.settings = settings or default_settings()

    def report(self, rows: list[dict], symbol: str) -> dict:
        symbol = symbol.upper()
        baseline_key = tuple(tuple(row[name] for name in FEATURES) for row in rows[:BASELINE])
        key = (baseline_key, len(rows), rows[-1]["event"] if rows else 0)
        with self.lock:
            cached = self.cache.get(symbol)
            if cached and cached[0] == key:
                return deepcopy(cached[1])
            model = None
            if len(rows) > BASELINE:
                prior = self.models.get(symbol)
                if prior and prior[0] == baseline_key:
                    model = prior[1]
                else:
                    model = CalibratedBaseline(np.array(baseline_key, dtype=float))
                    self.models[symbol] = (baseline_key, model)
            result = _report(rows, symbol, model, self.settings)
            self.cache[symbol] = (key, result)
            return deepcopy(result)


def report(session: ExchangeSession, symbol: str = "RELIANCE") -> dict:
    rows = [row.copy() for row in session.observations if row["symbol"] == symbol.upper()]
    return ExecutionMonitor().report(rows, symbol)


def _report(rows: list[dict], symbol: str, model: CalibratedBaseline | None, settings: Settings) -> dict:
    output = {"symbol": symbol.upper(), "observations": len(rows), "baseline_size": BASELINE,
              "status": "warming_up", "alerts": [], "timeline": [], "flagged": 0,
              "features": list(FEATURES), "note": NOTE, "source": "Local matching-engine executions",
              "model_version": MODEL_VERSION, "method": "Isolation Forest + calibrated robust guards",
              "calibration": {"fit_observations": FIT_SIZE, "cutoff_observations": BASELINE - FIT_SIZE,
                              "forest_margin": settings.forest_margin, "guard_floor": settings.guard_floor,
                              "guard_padding": settings.guard_padding,
                              "forest_confirmation": settings.forest_confirmation,
                              "size_multiplier": settings.size_multiplier,
                              "evidence": "Controlled matching-engine workloads; not labelled real-market fraud"}}
    if len(rows) <= BASELINE:
        return output
    matrix = np.array([[row[name] for name in FEATURES] for row in rows], dtype=float)
    heldout = matrix[BASELINE:]
    forest_flags, guard_flags, envelope_flags, scores, z, forest_scores, ratios = model.score(heldout, settings)
    forest_threshold, guard_threshold = model.thresholds(settings)
    output["calibration"].update(forest_threshold=round(forest_threshold, 6),
                                 robust_threshold=round(guard_threshold, 6),
                                 varying_features=model.varying_features,
                                 baseline_warning="Low-variation baseline: forest sensitivity is limited; robust guards remain active." if model.varying_features < 3 else "Baseline normality is assumed, not verified.")
    timeline = []
    for index, row in enumerate(rows[BASELINE:]):
        names = [FEATURES[j] for j in np.argsort(z[index])[::-1][:3]]
        detectors = (["isolation_forest"] if forest_flags[index] else []) + (["robust_guard"] if guard_flags[index] else []) + (["size_envelope"] if envelope_flags[index] else [])
        unusual = bool(detectors)
        timeline.append({**row, "needs_review": unusual,
                         "score": round(float(scores[index]), 4), "detectors": detectors,
                         "forest_unusualness": round(float(forest_scores[index]), 6),
                         "max_robust_deviation": round(float(z[index].max()), 4),
                         "max_count_ratio": round(float(ratios[index].max()), 4),
                         "reasons": names, "message": "Unusual execution; review suggested" if unusual else "Within calibrated baseline limits"})
    output.update(status="monitoring", timeline=timeline[-200:],
                  alerts=[row for row in timeline if row["needs_review"]][-100:],
                  flagged=sum(row["needs_review"] for row in timeline), scored=len(timeline))
    return output
