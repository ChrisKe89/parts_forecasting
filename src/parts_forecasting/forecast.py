from __future__ import annotations

import pandas as pd

from parts_forecasting.config import (
    DEFAULT_FORECAST_HORIZON_MONTHS,
    SPARSE_DAMPING_FACTOR,
    SPARSE_USAGE_THRESHOLD,
    VOLATILITY_CV_THRESHOLD,
    VOLATILITY_DAMPING_FACTOR,
)


def calculate_forecast_metrics(features_df: pd.DataFrame, forecast_horizon_months: int = DEFAULT_FORECAST_HORIZON_MONTHS) -> pd.DataFrame:
    df = features_df.copy()
    df["training_months"] = df["training_months"].clip(lower=1)
    df["avg_monthly_usage"] = df["training_usage_qty"] / df["training_months"]
    df["std_dev_monthly_usage"] = df["std_dev_monthly_usage"].fillna(0)
    df["coefficient_of_variation"] = 0.0
    non_zero = df["avg_monthly_usage"] > 0
    df.loc[non_zero, "coefficient_of_variation"] = df.loc[non_zero, "std_dev_monthly_usage"] / df.loc[non_zero, "avg_monthly_usage"]

    df["monthly_usage_rate_per_machine"] = 0.0
    valid_installed = df["avg_installed_base"] > 0
    df.loc[valid_installed, "monthly_usage_rate_per_machine"] = (
        df.loc[valid_installed, "training_usage_qty"] / df.loc[valid_installed, "avg_installed_base"] / df.loc[valid_installed, "training_months"]
    )

    df["raw_predicted_demand"] = (
        df["monthly_usage_rate_per_machine"] * df["installed_base_at_forecast"] * forecast_horizon_months
    )
    df["adjusted_predicted_demand"] = df["raw_predicted_demand"]
    df["demand_classification"] = "normal"
    df["forecast_reason"] = "time_normalized_usage_rate"

    no_hist = df["training_usage_qty"] == 0
    sparse = (df["training_usage_qty"] > 0) & (df["training_usage_qty"] < SPARSE_USAGE_THRESHOLD)
    volatile = df["coefficient_of_variation"] > VOLATILITY_CV_THRESHOLD

    df.loc[no_hist, ["adjusted_predicted_demand", "demand_classification", "forecast_reason"]] = [0.0, "no_history", "no historical usage"]
    df.loc[sparse, "adjusted_predicted_demand"] = df.loc[sparse, "raw_predicted_demand"] * SPARSE_DAMPING_FACTOR
    df.loc[sparse, "demand_classification"] = "sparse"
    df.loc[sparse, "forecast_reason"] = "sparse history damped"
    df.loc[volatile & ~no_hist, "adjusted_predicted_demand"] = df.loc[volatile & ~no_hist, "adjusted_predicted_demand"] * VOLATILITY_DAMPING_FACTOR
    df.loc[volatile & ~no_hist, "demand_classification"] = "volatile"
    df.loc[volatile & ~no_hist, "forecast_reason"] = "high variability damped"

    return df.fillna(0)
