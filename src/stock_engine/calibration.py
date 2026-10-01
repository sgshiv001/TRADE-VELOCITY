"""Offline, controlled calibration workloads. Never used to seed the app."""

from dataclasses import asdict
from itertools import product
import platform
from random import Random
from time import perf_counter

import numpy as np
import sklearn
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .session import ExchangeSession
from .watchdog import BASELINE, FEATURES, MODEL_VERSION, CalibratedBaseline, Settings

PROFILES = ("varied_small", "repeated_small", "constant_small", "high_volume", "fragmented", "balanced_book")
DEVELOPMENT_SEEDS = tuple(range(100, 108))
# The former holdout is now regression evidence, not an untouched test set.
REGRESSION_SEEDS = tuple(range(2000, 2016))
HELDOUT_SEEDS = tuple(range(3000, 3032))
NORMAL_COUNT = 80
DEVIATIONS = ("quantity_spike", "price_jump_up", "price_jump_down", "fragmentation_burst",
              "depth_surge", "large_unfilled_submission", "combined_spike", "missed_case_regression")


def execute(session, index, quantity, price, *, pieces=1, bid_depth=0, ask_depth=0, partial=None, side="BUY"):
    for order in session.engine.active_orders():
        session.cancel_order(order["order_id"])
    if bid_depth:
        session.place_order(f"N-B-{index}", "RELIANCE", "BUY", bid_depth, f"{price * .8:.2f}")
    if ask_depth:
        session.place_order(f"N-S-{index}", "RELIANCE", "SELL", ask_depth, f"{price * 1.2:.2f}")
    available = partial or quantity
    pieces = min(pieces, available)
    for piece in range(pieces):
        shares = available // pieces + int(piece < available % pieces)
        session.place_order(f"M-{index}-{piece}", "RELIANCE", "SELL" if side == "BUY" else "BUY", shares, f"{price:.2f}")
    session.place_order(f"T-{index}", "RELIANCE", side, quantity, f"{price:.2f}")


def workload(profile: str, seed: int):
    """Emit actual engine executions and known controlled-deviation labels."""
    if profile not in PROFILES:
        raise ValueError("unknown calibration profile")
    rng, session = Random(seed), ExchangeSession()
    for index in range(BASELINE + NORMAL_COUNT):
        if profile == "constant_small": quantity, price = 25, 100.0
        elif profile == "repeated_small": quantity, price = 10 + index % 17, 100 + (index % 5 - 2) / 10
        elif profile == "high_volume": quantity, price = rng.randrange(2000,8001), 100 + rng.randrange(-2,3) / 10
        elif profile == "fragmented": quantity, price = rng.randrange(100,301), 100 + rng.randrange(-2,3) / 10
        else: quantity, price = rng.randrange(10,50), 100 + rng.randrange(-2,3) / 10
        pieces = rng.randrange(2,6) if profile == "fragmented" else 1
        bid = rng.randrange(100,601) if profile == "balanced_book" else 0
        ask = rng.randrange(100,601) if profile == "balanced_book" else 0
        execute(session,index,quantity,price,pieces=pieces,bid_depth=bid,ask_depth=ask,side="SELL" if profile == "balanced_book" and index % 2 else "BUY")
    ordinary_quantity = 4000 if profile == "high_volume" else 150 if profile == "fragmented" else 25
    for offset, kind in enumerate(DEVIATIONS):
        quantity, price, pieces, bid, ask, partial = ordinary_quantity, 100.0, 1, 0, 0, None
        if kind == "quantity_spike": quantity = ordinary_quantity * 100
        elif kind == "price_jump_up": price = 125.0
        elif kind == "price_jump_down": price = 75.0
        elif kind == "fragmentation_burst": quantity, pieces = max(60,ordinary_quantity), 60
        elif kind == "depth_surge": bid = ask = 100_000
        elif kind == "large_unfilled_submission": quantity, partial = 1_000_000, ordinary_quantity
        elif kind == "combined_spike": quantity, price = ordinary_quantity * 100, 130.0
        elif kind == "missed_case_regression": quantity, price = max(5000,ordinary_quantity * 50), 130.0
        execute(session,BASELINE + NORMAL_COUNT + offset,quantity,price,pieces=pieces,bid_depth=bid,ask_depth=ask,partial=partial)
    assert len(session.observations) == BASELINE + NORMAL_COUNT + len(DEVIATIONS)
    return session.observations, [False] * NORMAL_COUNT + [True] * len(DEVIATIONS)


def prepare(profile, seed):
    rows, labels = workload(profile,seed)
    matrix = np.array([[row[feature] for feature in FEATURES] for row in rows], dtype=float)
    baseline = CalibratedBaseline(matrix[:BASELINE])
    forest, deviations = baseline.components(matrix[BASELINE:])
    return {"profile":profile,"seed":seed,"labels":np.array(labels),"baseline":baseline,
            "forest":forest,"guard":deviations.max(axis=1),"matrix":matrix,
            "ratio":baseline.count_ratios(matrix[BASELINE:]).max(axis=1)}


def predict(case, settings):
    forest_threshold, guard_threshold = case["baseline"].thresholds(settings)
    return ((case["forest"] > forest_threshold) & (case["guard"] > settings.forest_confirmation)) | (case["guard"] > guard_threshold) | (case["ratio"] > settings.size_multiplier)


def metrics(cases, predictions):
    actual, predicted = np.concatenate([case["labels"] for case in cases]), np.concatenate(predictions)
    tp, fp = int((actual & predicted).sum()), int((~actual & predicted).sum())
    fn, tn = int((actual & ~predicted).sum()), int((~actual & ~predicted).sum())
    return {"true_positives":tp,"false_positives":fp,"false_negatives":fn,"true_negatives":tn,
            "normal_observations":tn+fp,"injected_deviations":tp+fn,
            "precision":tp/(tp+fp) if tp+fp else 0.0,"recall":tp/(tp+fn) if tp+fn else 0.0,
            "f1":2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.0,"false_positive_rate":fp/(fp+tn) if fp+tn else 0.0}


def evaluate(progress=None):
    started = perf_counter()
    development = []
    for profile in PROFILES:
        development.extend(prepare(profile,seed) for seed in DEVELOPMENT_SEEDS)
        if progress: progress(f"Development baseline fitted: {profile}")
    candidates = []
    for margin,floor,confirmation,multiplier in product((.03,.05,.08),(5.0,6.0,8.0),(2.0,3.0,4.0),(10.0,20.0)):
        settings = Settings(margin,floor,1.0,confirmation,multiplier)
        result = metrics(development,[predict(case,settings) for case in development])
        candidates.append({"settings":asdict(settings),"metrics":result})
    eligible = [candidate for candidate in candidates if candidate["metrics"]["false_positive_rate"] <= .02]
    if not eligible:
        raise RuntimeError("No development candidate met the 2% controlled false-alarm budget")
    selected = max(eligible,key=lambda candidate:(candidate["metrics"]["recall"],-candidate["metrics"]["false_positive_rate"],candidate["settings"]["forest_margin"],candidate["settings"]["guard_floor"],candidate["settings"]["forest_confirmation"],candidate["settings"]["size_multiplier"]))
    settings = Settings(**selected["settings"])
    # No held-out workload is even generated until parameter selection finishes.
    heldout, legacy_predictions = [], []
    for profile in PROFILES:
        for seed in HELDOUT_SEEDS:
            case = prepare(profile,seed)
            heldout.append(case)
            legacy = make_pipeline(StandardScaler(),IsolationForest(n_estimators=150,contamination=.05,random_state=42))
            legacy.fit(case["matrix"][:BASELINE])
            legacy_predictions.append(legacy.decision_function(case["matrix"][BASELINE:]) < 0)
        if progress: progress(f"Held-out comparison finished: {profile}")
    predictions = [predict(case,settings) for case in heldout]
    by_profile = {profile:metrics([case for case in heldout if case["profile"] == profile],
                                  [prediction for case,prediction in zip(heldout,predictions) if case["profile"] == profile]) for profile in PROFILES}
    by_deviation = {kind:{"detected":sum(bool(prediction[NORMAL_COUNT + index]) for prediction in predictions),"total":len(heldout)} for index,kind in enumerate(DEVIATIONS)}
    errors = []
    detector_breakdown = {kind:{"forest_only":0,"guard_only":0,"both":0,"neither":0}
                          for kind in ("normal", "injected_deviation")}
    for case, prediction in zip(heldout,predictions):
        forest_threshold, guard_threshold = case["baseline"].thresholds(settings)
        for index, (actual, predicted) in enumerate(zip(case["labels"],prediction)):
            forest = bool(case["forest"][index] > forest_threshold and case["guard"][index] > settings.forest_confirmation)
            guard = bool(case["guard"][index] > guard_threshold or case["ratio"][index] > settings.size_multiplier)
            channel = "both" if forest and guard else "forest_only" if forest else "guard_only" if guard else "neither"
            detector_breakdown["injected_deviation" if actual else "normal"][channel] += 1
            if bool(actual) != bool(predicted):
                errors.append({"profile":case["profile"],"seed":case["seed"],"observation":BASELINE+index+1,
                               "kind":DEVIATIONS[index-NORMAL_COUNT] if actual else "normal_control",
                               "expected_review":bool(actual),"predicted_review":bool(predicted),
                               "features":dict(zip(FEATURES,case["matrix"][BASELINE+index].tolist())),
                               "forest_unusualness":float(case["forest"][index]),"forest_threshold":forest_threshold,
                               "robust_deviation":float(case["guard"][index]),"robust_threshold":guard_threshold})
    regressions = [prepare(profile,seed) for profile in PROFILES for seed in REGRESSION_SEEDS]
    if progress: progress("Previous holdout checked as regression evidence only")
    return {"model_version":MODEL_VERSION,"scope":"Synthetic, controlled executions from the actual matching engine; NOT real-market fraud accuracy",
            "protocol":{"profiles":list(PROFILES),"development_seeds":list(DEVELOPMENT_SEEDS),"heldout_seeds":list(HELDOUT_SEEDS),
                        "fit_observations":24,"cutoff_observations":16,"normal_suffix_per_stream":NORMAL_COUNT,
                        "deviations_per_stream":len(DEVIATIONS),"false_alarm_budget":.02,
                        "selection":"Max development recall within <=2% false alarms; ties: lower false alarms, larger forest margin, robust floor, forest confirmation and size multiplier",
                        "previous_holdout_now_regression_seeds":list(REGRESSION_SEEDS),
                        "heldout_used_for_tuning":False},
            "selected_settings":asdict(settings),"development":selected["metrics"],"candidates":candidates,
            "heldout":metrics(heldout,predictions),"legacy_heldout":metrics(heldout,legacy_predictions),
            "previous_holdout_regression":metrics(regressions,[predict(case,settings) for case in regressions]),
            "by_profile":by_profile,"by_deviation":by_deviation,
            "error_cases":errors,"detector_breakdown":detector_breakdown,
            "limitations":["Baseline normality is assumed; poisoned or unrepresentative baselines can cause misses or false alerts.",
                           "Synthetic profiles and extreme injected deviations do not represent the diversity or prevalence of real market abuse.",
                           "Constant and repetitive profiles are deterministic across seeds; stream counts are not independent statistical evidence.",
                           "Severity is not a probability. Reviewed/dismissed alerts do not automatically retrain the detector.",
                           "Daily-history anomaly analysis remains separate and is not validated by this experiment."],
            "runtime":{"python":platform.python_version(),"scikit_learn":sklearn.__version__,"platform":platform.platform(),"elapsed_seconds":round(perf_counter()-started,3)}}
