import pandas as pd

from src.backtest import run_rolling_backtest
from src.feature_engineering import build_installed_base
from src.main import summarize_results


def _monthly_frame(start="2024-01-01", periods=24, qty=1):
    months = pd.date_range(start, periods=periods, freq="MS")
    return pd.DataFrame({"month": months, "qty": [qty] * periods})


def test_run_rolling_backtest_produces_required_output_columns_and_windows():
    usage = _monthly_frame()
    usage["part_number"] = "P1"
    usage["model"] = "M1"
    usage = usage[["part_number", "model", "month", "qty"]]

    installs = _monthly_frame(qty=5)
    installs["model"] = "M1"
    installs = installs[["model", "month", "qty"]]

    monthly_data = {
        "usage": usage,
        "installs": installs,
        "emergency": pd.DataFrame(columns=["part_number", "model", "month", "qty"]),
        "cannibalised": pd.DataFrame(columns=["part_number", "model", "month", "qty"]),
        "stock": pd.DataFrame(columns=["part_number", "stock_on_hand", "stock_on_order", "snapshot_date"]),
        "mapping": pd.DataFrame({"part_number": ["P1"], "model": ["M1"]}),
    }

    installed_base = build_installed_base(installs)
    result = run_rolling_backtest(monthly_data, installed_base)

    expected_cols = {
        "forecast_date", "part_number", "model", "training_start", "training_end", "lead_time_start", "lead_time_end",
        "evaluation_start", "evaluation_end", "predicted_demand", "true_demand", "recommended_order", "safety_buffer",
        "forecast_error", "absolute_error", "under_forecast_qty", "over_forecast_qty",
    }

    assert not result.empty
    assert set(result.columns) == expected_cols
    assert (result["evaluation_start"] == result["lead_time_end"]).all()
    assert (result["evaluation_end"] > result["evaluation_start"]).all()


def test_summarize_results_aggregates_error_metrics():
    results = pd.DataFrame(
        {
            "absolute_error": [1.0, 3.0],
            "under_forecast_qty": [2.0, 0.0],
            "over_forecast_qty": [0.0, 4.0],
            "predicted_demand": [10.0, 20.0],
            "true_demand": [9.0, 24.0],
        }
    )

    summary = summarize_results(results)

    assert summary.iloc[0]["mae"] == 2.0
    assert summary.iloc[0]["total_under_forecast"] == 2.0
    assert summary.iloc[0]["total_over_forecast"] == 4.0
    assert summary.iloc[0]["mean_predicted_demand"] == 15.0
    assert summary.iloc[0]["mean_true_demand"] == 16.5
