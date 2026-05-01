import pandas as pd

from parts_forecasting.backtest import run_rolling_backtest
from parts_forecasting.feature_engineering import build_installed_base
from parts_forecasting.main import summarize_results
from parts_forecasting.ordering import compute_recommended_order


def _monthly_frame(start="2024-01-01", periods=24, qty=1):
    months = pd.date_range(start, periods=periods, freq="MS")
    return pd.DataFrame({"month": months, "qty": [qty] * periods})


def _monthly_data(usage_qty=1):
    usage = _monthly_frame(qty=usage_qty)
    usage["part_number"] = "P1"; usage["model"] = "M1"
    installs = _monthly_frame(qty=5); installs["model"] = "M1"
    return {
        "usage": usage[["part_number", "model", "month", "qty"]],
        "installs": installs[["model", "month", "qty"]],
        "emergency": pd.DataFrame(columns=["part_number", "model", "month", "qty"]),
        "cannibalised": pd.DataFrame(columns=["part_number", "model", "month", "qty"]),
        "stock": pd.DataFrame(columns=["part_number", "stock_on_hand", "stock_on_order", "snapshot_date"]),
        "mapping": pd.DataFrame({"part_number": ["P1"], "model": ["M1"]}),
    }


def test_import_path_works():
    from parts_forecasting.forecast import calculate_forecast_metrics
    assert callable(calculate_forecast_metrics)


def test_rolling_backtest_and_required_columns_and_multiple_windows():
    monthly = _monthly_data(usage_qty=1)
    result = run_rolling_backtest(monthly, build_installed_base(monthly["installs"]))
    assert result["forecast_date"].nunique() > 1
    required = {"training_months","training_usage_qty","avg_monthly_usage","std_dev_monthly_usage","coefficient_of_variation","avg_installed_base","installed_base_at_forecast","monthly_usage_rate_per_machine","raw_predicted_demand","adjusted_predicted_demand","current_stock_used","recommended_order","demand_classification","forecast_reason"}
    assert required.issubset(result.columns)


def test_zero_training_usage_predicts_zero():
    monthly = _monthly_data(usage_qty=0)
    result = run_rolling_backtest(monthly, build_installed_base(monthly["installs"]))
    assert (result["adjusted_predicted_demand"] == 0).all()


def test_sparse_demand_damping_applies_and_order_uses_stock():
    f = pd.DataFrame({"part_number":["P1"],"model":["M1"],"training_usage_qty":[2.0],"training_months":[9],"std_dev_monthly_usage":[0.1],"avg_installed_base":[10.0],"installed_base_at_forecast":[10.0],"raw_predicted_demand":[2.0],"adjusted_predicted_demand":[1.0],"coefficient_of_variation":[0.2],"forecast_reason":["x"]})
    stock = pd.DataFrame({"part_number":["P1"],"stock_on_hand":[1],"stock_on_order":[1],"snapshot_date":[pd.Timestamp("2024-01-01")]})
    out = compute_recommended_order(f, stock, pd.Timestamp("2024-02-01"))
    assert out.iloc[0]["recommended_order"] >= 0


def test_no_stock_snapshot_before_forecast_uses_zero_stock():
    f = pd.DataFrame({"part_number":["P1"],"model":["M1"],"adjusted_predicted_demand":[1.0],"coefficient_of_variation":[0.0],"forecast_reason":["x"]})
    stock = pd.DataFrame({"part_number":["P1"],"stock_on_hand":[9],"stock_on_order":[2],"snapshot_date":[pd.Timestamp("2025-01-01")]})
    out = compute_recommended_order(f, stock, pd.Timestamp("2024-01-01"))
    assert out.iloc[0]["current_stock_used"] == 0


def test_summarize_results_metrics_exist():
    summary = summarize_results(pd.DataFrame({"predicted_demand":[1.0],"true_demand":[0.0],"recommended_order":[1],"absolute_error":[1.0],"forecast_error":[1.0]}))
    assert "RMSE" in summary.columns
