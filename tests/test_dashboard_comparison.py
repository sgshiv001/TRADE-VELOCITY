from pathlib import Path

from streamlit.testing.v1 import AppTest


DASHBOARD = Path(__file__).resolve().parents[1] / "dashboard.py"


def test_comparison_runs_without_changing_session_and_survives_reruns():
    app = AppTest.from_file(str(DASHBOARD)).run(timeout=30)
    next(button for button in app.button if button.label == "Load example market").click().run(timeout=30)
    events = app.session_state.exchange.to_dict()
    before = app.session_state.exchange.engine.active_orders()
    next(widget for widget in app.number_input if widget.label == "Comparison commands").set_value(100)
    next(widget for widget in app.selectbox if widget.label == "Comparison workload").select("deep")
    next(button for button in app.button if button.label == "Run comparison").click().run(timeout=30)

    assert not app.exception
    assert app.session_state.exchange.to_dict() == events
    assert app.session_state.exchange.engine.active_orders() == before
    results = app.session_state.comparison_results
    assert len(results) == 6
    assert {row["engine"] for row in results} == {"indexed", "linear"}
    assert all(row["commands"] == 100 and row["trades"] == 50 for row in results)

    app.run(timeout=30)
    assert not app.exception
    assert app.session_state.comparison_results == results
