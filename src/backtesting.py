from __future__ import annotations

import pandas as pd
from forecasting.engine import run_forecast


def run_backtest(data: dict[str, pd.DataFrame], train_months: int = 9, test_months: int = 3) -> pd.DataFrame:
    usage = data["usage"].copy()
    end = usage["usage_date"].max()
    test_start = end - pd.DateOffset(months=test_months) + pd.DateOffset(days=1)
    train_start = test_start - pd.DateOffset(months=train_months)
    train_usage = usage[(usage.usage_date >= train_start) & (usage.usage_date < test_start)]
    test_usage = usage[(usage.usage_date >= test_start) & (usage.usage_date <= end)]
    forecast_df = run_forecast({**data, "usage": train_usage}, as_of_date=train_usage["usage_date"].max())
    actual = test_usage.groupby(["part_id", "model"], as_index=False)["usage_qty"].sum().rename(columns={"usage_qty": "actual_usage"})
    merged = forecast_df.merge(actual, on=["part_id", "model"], how="left").fillna({"actual_usage": 0})
    merged["forecast_error"] = merged["install_adjusted_forecast"] - merged["actual_usage"]
    merged["absolute_forecast_error"] = merged["forecast_error"].abs()
    merged["percent_error"] = merged.apply(lambda r: (r["forecast_error"] / r["actual_usage"] * 100.0) if r["actual_usage"] else 0.0, axis=1)
    merged["mae"] = merged["absolute_forecast_error"].mean()
    return merged
