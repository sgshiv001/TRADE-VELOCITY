from pathlib import Path

from streamlit.testing.v1 import AppTest


DASHBOARD = Path(__file__).resolve().parents[1] / "dashboard.py"


def click(app: AppTest, label: str) -> None:
    next(button for button in app.button if button.label == label).click().run(timeout=30)


def test_dashboard_loads_demo_and_displays_trades():
    app = AppTest.from_file(str(DASHBOARD)).run(timeout=30)
    click(app, "Load example market")

    assert not app.exception
    assert len(app.session_state.exchange.events) == 9
    assert len(app.session_state.exchange.engine.trades()) == 4


def test_dashboard_place_and_cancel_workflow():
    app = AppTest.from_file(str(DASHBOARD)).run(timeout=30)
    click(app, "Place order")
    assert not app.exception
    assert len(app.session_state.exchange.engine.active_orders()) == 1

    click(app, "Cancel order")
    assert not app.exception
    assert app.session_state.exchange.engine.active_orders() == []
    assert [event["type"] for event in app.session_state.exchange.events] == ["place", "cancel"]
