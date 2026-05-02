import pandas as pd

from backtesting import run_backtest
from data.synthetic_generator import generate_synthetic_data
from forecasting.calculations import service_level_to_z
from forecasting.engine import run_forecast
from utils.config import ForecastingConfig


def test_service_level_lookup_values():
    assert round(service_level_to_z(0.90), 4) == 1.2816
    assert round(service_level_to_z(0.99), 4) == 2.3263


def test_outlier_adjustment_reduces_spike_impact():
    data = {
        "parts": pd.DataFrame([{"part_id": "P1", "part_name": "x", "model": "M1", "smoothing_group": "A", "minimum_order_quantity": 1, "lead_time_days": 90}]),
        "usage": pd.DataFrame([
            {"part_id": "P1", "model": "M1", "usage_date": pd.Timestamp("2025-01-01"), "usage_qty": 5, "active_machines": 10},
            {"part_id": "P1", "model": "M1", "usage_date": pd.Timestamp("2025-02-01"), "usage_qty": 6, "active_machines": 10},
            {"part_id": "P1", "model": "M1", "usage_date": pd.Timestamp("2025-03-01"), "usage_qty": 1000, "active_machines": 10},
            {"part_id": "P1", "model": "M1", "usage_date": pd.Timestamp("2025-04-01"), "usage_qty": 5, "active_machines": 10},
            {"part_id": "P1", "model": "M1", "usage_date": pd.Timestamp("2025-05-01"), "usage_qty": 6, "active_machines": 10},
            {"part_id": "P1", "model": "M1", "usage_date": pd.Timestamp("2025-06-01"), "usage_qty": 5, "active_machines": 10},
        ]),
        "installs": pd.DataFrame(columns=["part_id", "model", "install_date", "install_qty", "install_status", "projected_install_confidence"]),
        "stock": pd.DataFrame([{"part_id": "P1", "model": "M1", "snapshot_date": pd.Timestamp("2025-06-01"), "stock_on_hand": 10, "stock_on_order": 0, "expected_arrival_date": pd.Timestamp("2025-07-01")}]),
    }
    out = run_forecast(data, config=ForecastingConfig(z_threshold=2.0))
    assert out.iloc[0]["outlier_count"] >= 1
    assert out.iloc[0]["base_forecast"] < 100


def test_backtest_has_required_metrics(tmp_path):
    generate_synthetic_data(tmp_path, seed=7)
    from data.loader import load_inputs
    data = load_inputs(tmp_path)
    result = run_backtest(data, train_months=9, test_months=3)
    for c in ["mae", "rmse", "forecast_bias", "under_forecast_count", "over_forecast_count", "service_level_estimate", "stockout_count"]:
        assert c in result.columns
