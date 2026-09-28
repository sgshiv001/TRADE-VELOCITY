from stock_engine.anomaly import FEATURE_NAMES, build_features, detect_anomalies
from stock_engine.market_data import demo_market_data


def test_feature_engineering_returns_required_numeric_features():
    data = demo_market_data()
    features = build_features(data.histories["RELIANCE"])

    assert list(features.columns) == list(FEATURE_NAMES)
    assert len(features) > 100
    assert features.isna().sum().sum() == 0


def test_isolation_forest_report_is_serializable_and_bounded():
    data = demo_market_data()
    report = detect_anomalies(data.histories, "RELIANCE", "1Y")

    assert report["model"] == "Isolation Forest"
    assert report["observations"] >= 10
    assert 0 <= report["latest"]["anomaly_score"] <= 1
    assert report["latest"]["date"]
    assert len(report["timeline"]) <= 90
    assert set(report["latest"]["features"]) == set(FEATURE_NAMES)


def test_unknown_anomaly_symbol_is_rejected():
    data = demo_market_data()

    try:
        detect_anomalies(data.histories, "UNKNOWN")
    except ValueError as exc:
        assert str(exc) == "company was not found"
    else:
        raise AssertionError("unknown symbols must be rejected")
