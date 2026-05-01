from __future__ import annotations

import numpy as np
import pandas as pd

from parts_forecasting.config import BACKTEST_TRAINING_WINDOW_MONTHS, DEFAULT_FORECAST_HORIZON_MONTHS, EVALUATION_WINDOW_DAYS, LEAD_TIME_DAYS
from parts_forecasting.forecast import calculate_forecast_metrics
from parts_forecasting.ordering import compute_recommended_order


def _true_demand_for_window(usage_monthly, emergency_monthly, cannibalised_monthly, evaluation_start, evaluation_end):
    def slice_sum(df):
        if df.empty:
            return pd.DataFrame(columns=["part_number", "model", "qty"])
        sliced = df[(df["month"] >= evaluation_start) & (df["month"] < evaluation_end)]
        return sliced.groupby(["part_number", "model"], as_index=False)["qty"].sum()

    usage_sum = slice_sum(usage_monthly)
    emergency_sum = slice_sum(emergency_monthly)
    cannibalised_sum = slice_sum(cannibalised_monthly)
    td = usage_sum.merge(emergency_sum, on=["part_number", "model"], how="outer", suffixes=("_usage", "_emergency"))
    td = td.merge(cannibalised_sum, on=["part_number", "model"], how="outer").fillna(0)
    td["true_demand"] = td["qty_usage"] + td["qty_emergency"] + td["qty"]
    return td[["part_number", "model", "true_demand"]]


def _build_features(part_model, usage, installs, installed_base_df, forecast_date, train_months):
    train_start = forecast_date - pd.DateOffset(months=train_months)
    training = usage[(usage["month"] >= train_start) & (usage["month"] < forecast_date)]
    grp = training.groupby(["part_number", "model"], as_index=False)["qty"]
    usage_totals = grp.sum().rename(columns={"qty": "training_usage_qty"})
    usage_std = grp.std().fillna(0).rename(columns={"qty": "std_dev_monthly_usage"})

    avg_base = (
        installed_base_df[(installed_base_df["month"] >= train_start) & (installed_base_df["month"] < forecast_date)]
        .groupby("model", as_index=False)["installed_base"].mean().rename(columns={"installed_base": "avg_installed_base"})
    )
    at_t = (
        installed_base_df[installed_base_df["month"] < forecast_date].sort_values(["model", "month"]).groupby("model", as_index=False).tail(1)
        [["model", "installed_base"]].rename(columns={"installed_base": "installed_base_at_forecast"})
    )

    f = part_model.merge(usage_totals, on=["part_number", "model"], how="left").merge(usage_std, on=["part_number", "model"], how="left")
    f = f.merge(avg_base, on="model", how="left").merge(at_t, on="model", how="left")
    f["training_months"] = train_months
    return f.fillna(0)


def run_rolling_backtest(monthly_data, installed_base_df, training_window_months=BACKTEST_TRAINING_WINDOW_MONTHS, forecast_horizon_months=DEFAULT_FORECAST_HORIZON_MONTHS):
    usage = monthly_data["usage"]
    part_model = monthly_data["mapping"].drop_duplicates()
    if usage.empty or part_model.empty:
        return pd.DataFrame()
    results = []
    for forecast_date in sorted(usage["month"].unique()):
        if usage[usage["month"] < forecast_date]["month"].nunique() < training_window_months:
            continue
        lead_time_end = forecast_date + pd.Timedelta(days=LEAD_TIME_DAYS)
        evaluation_end = lead_time_end + pd.Timedelta(days=EVALUATION_WINDOW_DAYS)
        if usage[usage["month"] >= evaluation_end].empty:
            continue
        features = _build_features(part_model, usage, monthly_data["installs"], installed_base_df, forecast_date, training_window_months)
        forecasts = calculate_forecast_metrics(features, forecast_horizon_months)
        orders = compute_recommended_order(forecasts, monthly_data["stock"], forecast_date)
        true_demand = _true_demand_for_window(usage, monthly_data["emergency"], monthly_data["cannibalised"], lead_time_end, evaluation_end)
        merged = orders.merge(true_demand, on=["part_number", "model"], how="left").fillna({"true_demand": 0})
        merged["predicted_demand"] = merged["adjusted_predicted_demand"]
        merged["forecast_error"] = merged["predicted_demand"] - merged["true_demand"]
        merged["absolute_error"] = merged["forecast_error"].abs()
        merged["under_forecast_qty"] = (merged["true_demand"] - merged["predicted_demand"]).clip(lower=0)
        merged["over_forecast_qty"] = (merged["predicted_demand"] - merged["true_demand"]).clip(lower=0)
        merged["forecast_date"] = forecast_date
        merged["training_start"] = forecast_date - pd.DateOffset(months=training_window_months)
        merged["training_end"] = forecast_date
        merged["lead_time_start"] = forecast_date
        merged["lead_time_end"] = lead_time_end
        merged["evaluation_start"] = lead_time_end
        merged["evaluation_end"] = evaluation_end
        results.append(merged)
    if not results:
        return pd.DataFrame()
    out = pd.concat(results, ignore_index=True).replace([np.inf, -np.inf], 0).fillna(0)
    return out
