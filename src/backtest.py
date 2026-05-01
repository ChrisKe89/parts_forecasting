"""Lead-time-aware rolling backtest."""

from __future__ import annotations

import pandas as pd

from src.config import EVALUATION_WINDOW_DAYS, LEAD_TIME_DAYS, TRAINING_WINDOW_MONTHS
from src.feature_engineering import compute_forecast_features
from src.forecast import calculate_predicted_demand
from src.ordering import compute_recommended_order


def _true_demand_for_window(
    usage_monthly: pd.DataFrame,
    emergency_monthly: pd.DataFrame,
    cannibalised_monthly: pd.DataFrame,
    evaluation_start: pd.Timestamp,
    evaluation_end: pd.Timestamp,
) -> pd.DataFrame:
    def slice_sum(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame(columns=["part_number", "model", "qty"])
        sliced = df[(df["month"] >= evaluation_start) & (df["month"] < evaluation_end)]
        return sliced.groupby(["part_number", "model"], as_index=False)["qty"].sum()

    usage_sum = slice_sum(usage_monthly)
    emergency_sum = slice_sum(emergency_monthly)
    cannibalised_sum = slice_sum(cannibalised_monthly)

    true_demand = usage_sum.merge(emergency_sum, on=["part_number", "model"], how="outer", suffixes=("_usage", "_emergency"))
    true_demand = true_demand.merge(cannibalised_sum, on=["part_number", "model"], how="outer")
    true_demand = true_demand.fillna(0)
    true_demand["true_demand"] = true_demand["qty_usage"] + true_demand["qty_emergency"] + true_demand["qty"]
    return true_demand[["part_number", "model", "true_demand"]]


def run_rolling_backtest(monthly_data: dict[str, pd.DataFrame], installed_base_df: pd.DataFrame) -> pd.DataFrame:
    usage = monthly_data["usage"]
    part_model = monthly_data["mapping"].drop_duplicates()

    if usage.empty or part_model.empty:
        return pd.DataFrame()

    all_months = sorted(usage["month"].unique())
    results = []

    for forecast_date in all_months:
        training_start = forecast_date - pd.DateOffset(months=TRAINING_WINDOW_MONTHS)
        lead_time_start = forecast_date
        lead_time_end = forecast_date + pd.Timedelta(days=LEAD_TIME_DAYS)
        evaluation_start = lead_time_end
        evaluation_end = lead_time_end + pd.Timedelta(days=EVALUATION_WINDOW_DAYS)

        if usage[usage["month"] < forecast_date]["month"].nunique() < TRAINING_WINDOW_MONTHS:
            continue
        if usage[usage["month"] >= evaluation_end].empty:
            continue

        features = compute_forecast_features(part_model, usage, monthly_data["installs"], installed_base_df, forecast_date)
        forecasts = calculate_predicted_demand(features)
        orders = compute_recommended_order(forecasts, monthly_data["stock"], forecast_date)

        true_demand = _true_demand_for_window(
            usage,
            monthly_data["emergency"],
            monthly_data["cannibalised"],
            evaluation_start,
            evaluation_end,
        )

        merged = orders.merge(true_demand, on=["part_number", "model"], how="left").fillna({"true_demand": 0})
        merged["forecast_error"] = merged["predicted_demand"] - merged["true_demand"]
        merged["absolute_error"] = merged["forecast_error"].abs()
        merged["under_forecast_qty"] = (merged["true_demand"] - merged["predicted_demand"]).clip(lower=0)
        merged["over_forecast_qty"] = (merged["predicted_demand"] - merged["true_demand"]).clip(lower=0)

        merged["forecast_date"] = forecast_date
        merged["training_start"] = training_start
        merged["training_end"] = forecast_date
        merged["lead_time_start"] = lead_time_start
        merged["lead_time_end"] = lead_time_end
        merged["evaluation_start"] = evaluation_start
        merged["evaluation_end"] = evaluation_end

        output_columns = [
            "forecast_date", "part_number", "model", "training_start", "training_end", "lead_time_start", "lead_time_end",
            "evaluation_start", "evaluation_end", "predicted_demand", "true_demand", "recommended_order", "safety_buffer",
            "forecast_error", "absolute_error", "under_forecast_qty", "over_forecast_qty",
        ]
        results.append(merged[output_columns])

    if not results:
        return pd.DataFrame()
    return pd.concat(results, ignore_index=True)
