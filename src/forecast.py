"""Forecast calculation module."""

from __future__ import annotations

import pandas as pd


def calculate_predicted_demand(features_df: pd.DataFrame) -> pd.DataFrame:
    forecast_df = features_df.copy()
    forecast_df["predicted_demand"] = (
        forecast_df["recent_usage_trend"]
        + forecast_df["installed_base_demand"]
        + forecast_df["growth_adjustment"]
    )
    return forecast_df
