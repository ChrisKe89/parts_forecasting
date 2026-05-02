import pandas as pd
from pathlib import Path

from forecasting.calculations import usage_per_machine, zscore_outliers, exponential_smoothing, holt_forecast, safety_stock
from inventory.logic import reorder_point, apply_moq, rolling_projected_stock
from data.synthetic_generator import generate_synthetic_data
from data.loader import load_inputs
from forecasting.engine import run_forecast
from backtesting import run_backtest


def test_usage_per_machine():
    df = pd.DataFrame({"part_id": ["p", "p"], "model": ["m", "m"], "usage_qty": [10, 20], "active_machines": [2, 3]})
    out = usage_per_machine(df)
    assert out.iloc[0]["usage_per_machine"] == 6


def test_zscore_and_outlier():
    s = pd.Series([1, 1, 1, 10])
    out = zscore_outliers(s, threshold=1.5)
    assert out["outlier_flag"].sum() == 1


def test_smoothing_and_holt():
    vals = [10, 12, 14, 16]
    assert exponential_smoothing(vals, 0.5) > 0
    f, t = holt_forecast(vals, 0.7, 0.2)
    assert f > vals[-1]
    assert t > 0


def test_safety_stock_and_rop_moq():
    ss = safety_stock(5, 90)
    rop = reorder_point(100, ss)
    assert rop > 100
    assert apply_moq(3, 10) == 10


def test_rolling_projection():
    sdf = pd.DataFrame({"snapshot_date": [pd.Timestamp("2026-01-01")], "stock_on_hand": [100], "stock_on_order": [50], "expected_arrival_date": [pd.Timestamp("2026-02-01")]})
    p = rolling_projected_stock(sdf, pd.Timestamp("2026-01-15"), 90, 5)
    assert p < 150


def test_synthetic_determinism(tmp_path: Path):
    d1 = generate_synthetic_data(tmp_path / "a", seed=42)
    d2 = generate_synthetic_data(tmp_path / "b", seed=42)
    assert d1["usage"].head(50).equals(d2["usage"].head(50))


def test_integration_pipeline(tmp_path: Path):
    generate_synthetic_data(tmp_path, seed=42)
    data = load_inputs(tmp_path)
    out = run_forecast(data)
    required = {"part_id", "model", "forecast_method_used", "reorder_point", "recommended_order_qty", "order_triggered"}
    assert required.issubset(set(out.columns))
    bt = run_backtest(data)
    assert {"mae", "forecast_error", "absolute_forecast_error", "percent_error"}.issubset(set(bt.columns))
