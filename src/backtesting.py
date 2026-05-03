from __future__ import annotations

import math
import pandas as pd

from .forecasting.engine import run_forecast


def _split_window(usage: pd.DataFrame, train_months: int, test_months: int) -> tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp]:
    end = usage["usage_date"].max()
    test_start = end - pd.DateOffset(months=test_months) + pd.DateOffset(days=1)
    train_start = test_start - pd.DateOffset(months=train_months)
    return train_start, test_start, end


def run_backtest(data: dict[str, pd.DataFrame], train_months: int = 21, test_months: int = 3) -> pd.DataFrame:
    usage = data["usage"].copy()
    train_start, test_start, end = _split_window(usage, train_months, test_months)

    train_usage = usage[(usage.usage_date >= train_start) & (usage.usage_date < test_start)]
    test_usage = usage[(usage.usage_date >= test_start) & (usage.usage_date <= end)]

    forecast_df = run_forecast({**data, "usage": train_usage}, as_of_date=train_usage["usage_date"].max())
    actual = test_usage.groupby(["part_number", "model"], as_index=False)["usage_qty"].sum().rename(columns={"usage_qty": "actual_usage"})
    merged = forecast_df.merge(actual, on=["part_number", "model"], how="left").fillna({"actual_usage": 0})

    merged["forecast_qty"] = merged["final_adjusted_demand"] * (test_months * 30 / 7)
    merged["forecast_error"] = merged["forecast_qty"] - merged["actual_usage"]
    merged["absolute_forecast_error"] = merged["forecast_error"].abs()
    merged["squared_forecast_error"] = merged["forecast_error"] ** 2
    merged["is_under_forecast"] = merged["forecast_error"] < 0
    merged["is_over_forecast"] = merged["forecast_error"] > 0
    merged["service_level_hit"] = merged["forecast_qty"] >= merged["actual_usage"]
    merged["stockout_risk"] = merged["projected_stock_at_arrival"] < 0

    mae = float(merged["absolute_forecast_error"].mean()) if not merged.empty else 0.0
    rmse = math.sqrt(float(merged["squared_forecast_error"].mean())) if not merged.empty else 0.0
    bias = float(merged["forecast_error"].mean()) if not merged.empty else 0.0

    merged["mae"] = mae
    merged["rmse"] = rmse
    merged["forecast_bias"] = bias
    merged["under_forecast_count"] = int(merged["is_under_forecast"].sum())
    merged["over_forecast_count"] = int(merged["is_over_forecast"].sum())
    merged["service_level_estimate"] = float(merged["service_level_hit"].mean()) if not merged.empty else 0.0
    merged["stockout_count"] = int(merged["stockout_risk"].sum())
    return merged
