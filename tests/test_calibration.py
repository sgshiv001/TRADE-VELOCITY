import json
from dataclasses import asdict
from pathlib import Path
import numpy as np
import pytest
from stock_engine.calibration import DEVELOPMENT_SEEDS, HELDOUT_SEEDS, REGRESSION_SEEDS, DEVIATIONS, NORMAL_COUNT, PROFILES, prepare, predict
from stock_engine.watchdog import BASELINE, default_settings


def test_calibration_and_heldout_seeds_are_disjoint():
    assert set(DEVELOPMENT_SEEDS).isdisjoint(HELDOUT_SEEDS)
    assert set(REGRESSION_SEEDS).isdisjoint(HELDOUT_SEEDS)


@pytest.mark.parametrize("profile",PROFILES)
def test_controlled_heldout_profile_catches_injected_deviations(profile):
    case = prepare(profile,3000)
    prediction = predict(case,default_settings())
    assert len(case["matrix"]) == BASELINE+NORMAL_COUNT+len(DEVIATIONS)
    assert np.mean(prediction[:NORMAL_COUNT]) <= .05
    assert prediction[-1]  # Previously missed large-execution regression.
    assert np.mean(prediction[NORMAL_COUNT:]) >= .875


def test_recorded_evaluation_matches_runtime_settings_and_declares_limits():
    path = Path(__file__).resolve().parents[1] / "benchmarks" / "ai-calibration.json"
    if not path.exists():
        pytest.skip("Full calibration artifact has not yet been generated")
    data = json.loads(path.read_text(encoding="utf-8"))
    settings = default_settings()
    assert data["selected_settings"] == asdict(settings)
    assert data["protocol"]["heldout_used_for_tuning"] is False
    assert "NOT real-market" in data["scope"]
    assert data["limitations"]
    assert len(data["error_cases"]) == data["heldout"]["false_positives"]+data["heldout"]["false_negatives"]
    assert sum(data["detector_breakdown"]["normal"].values()) == data["heldout"]["normal_observations"]
    assert sum(data["detector_breakdown"]["injected_deviation"].values()) == data["heldout"]["injected_deviations"]


@pytest.mark.parametrize("profile,seed", [("varied_small",2012),("varied_small",2015),
                                         ("high_volume",2015),("balanced_book",2002)])
def test_former_false_alerts_do_not_regress(profile,seed):
    case = prepare(profile,seed)
    assert not predict(case,default_settings())[:NORMAL_COUNT].any()
