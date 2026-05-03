import pandas as pd

from src.data.synthetic_generator import generate_synthetic_data
from src.backtesting import run_backtest
from src.forecasting.engine import run_forecast
from src.inventory.logic import apply_order_constraints


def test_synthetic_scale_and_baseline(tmp_path):
    data = generate_synthetic_data(tmp_path)
    assert data["parts"]["part_id"].nunique() == 1000
    assert data["machine_models"]["model_id"].nunique() == 50
    assert data["usage"]["week_start_date"].nunique() == 104
    assert 0.55 <= data["baseline_service_level"] <= 0.65


def test_moq_and_multiple_logic():
    x = apply_order_constraints(17, 10, 5)
    assert x["final_order_qty"] == 20 and x["order_multiple_applied"]
    y = apply_order_constraints(6, 10, 5)
    assert y["final_order_qty"] == 10 and y["moq_applied"]


def test_backtest_and_forecast_outputs(tmp_path):
    data = generate_synthetic_data(tmp_path)
    f = run_forecast(data)
    assert (f["demand_source"] == "usage_only").all()
    summary, weekly, concerns = run_backtest(data, enforce_fail_conditions=True)
    assert not summary.empty and not weekly.empty
    assert "concerns" in concerns
    assert weekly["part_id"].nunique() >= 950
