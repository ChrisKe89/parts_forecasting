"""Deterministic feature engineering for forecast points."""

from __future__ import annotations

import pandas as pd

from config import TRAINING_WINDOW_MONTHS


def build_installed_base(installs_monthly: pd.DataFrame) -> pd.DataFrame:
    if installs_monthly.empty:
        return installs_monthly
    installed_base = installs_monthly.sort_values(["model", "month"]).copy()
    installed_base["installed_base"] = installed_base.groupby("model")["qty"].cumsum()
    return installed_base


def compute_forecast_features(
    part_model_df: pd.DataFrame,
    usage_monthly: pd.DataFrame,
    installs_monthly: pd.DataFrame,
    installed_base_df: pd.DataFrame,
    forecast_date: pd.Timestamp,
) -> pd.DataFrame:
    training_start = forecast_date - pd.DateOffset(months=TRAINING_WINDOW_MONTHS)
    training_usage = usage_monthly[(usage_monthly["month"] >= training_start) & (usage_monthly["month"] < forecast_date)]
    recent_start = forecast_date - pd.DateOffset(months=3)
    recent_usage = usage_monthly[(usage_monthly["month"] >= recent_start) & (usage_monthly["month"] < forecast_date)]

    usage_totals = training_usage.groupby(["part_number", "model"], as_index=False)["qty"].sum().rename(columns={"qty": "training_usage_qty"})
    recent_avg = recent_usage.groupby(["part_number", "model"], as_index=False)["qty"].mean().rename(columns={"qty": "recent_monthly_avg"})

    avg_installed_base = (
        installed_base_df[(installed_base_df["month"] >= training_start) & (installed_base_df["month"] < forecast_date)]
        .groupby("model", as_index=False)["installed_base"]
        .mean()
        .rename(columns={"installed_base": "avg_installed_base"})
    )

    installed_base_at_t = (
        installed_base_df[installed_base_df["month"] < forecast_date]
        .sort_values(["model", "month"])
        .groupby("model", as_index=False)
        .tail(1)[["model", "installed_base"]]
        .rename(columns={"installed_base": "installed_base_at_t"})
    )

    installs_last_3 = (
        installs_monthly[(installs_monthly["month"] >= recent_start) & (installs_monthly["month"] < forecast_date)]
        .groupby("model", as_index=False)["qty"]
        .sum()
        .rename(columns={"qty": "installs_last_3_months"})
    )

    features = part_model_df.merge(usage_totals, on=["part_number", "model"], how="left")
    features = features.merge(recent_avg, on=["part_number", "model"], how="left")
    features = features.merge(avg_installed_base, on="model", how="left")
    features = features.merge(installed_base_at_t, on="model", how="left")
    features = features.merge(installs_last_3, on="model", how="left")

    features = features.fillna(0)
    features["recent_usage_trend"] = features["recent_monthly_avg"] * 3
    features["usage_rate"] = features["training_usage_qty"] / features["avg_installed_base"].replace(0, pd.NA)
    features["usage_rate"] = features["usage_rate"].fillna(0)
    features["usage_rate_90"] = features["usage_rate"] * 3
    features["installed_base_demand"] = features["installed_base_at_t"] * features["usage_rate_90"]
    features["growth_adjustment"] = features["installs_last_3_months"] * features["usage_rate_90"]

    return features
