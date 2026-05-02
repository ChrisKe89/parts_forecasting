from __future__ import annotations

import math
import pandas as pd


def usage_per_machine(usage_df: pd.DataFrame) -> pd.DataFrame:
    grouped = usage_df.groupby(["part_id", "model"], as_index=False).agg(
        total_part_usage=("usage_qty", "sum"),
        total_active_machines=("active_machines", "sum"),
    )
    grouped["usage_per_machine"] = grouped["total_part_usage"] / grouped["total_active_machines"].replace(0, pd.NA)
    return grouped.fillna(0)


def zscore_outliers(series: pd.Series, threshold: float = 3.0) -> pd.DataFrame:
    mean = float(series.mean())
    std = float(series.std(ddof=0))
    if std == 0:
        z = pd.Series([0.0] * len(series), index=series.index)
    else:
        z = (series - mean) / std
    return pd.DataFrame({"mean": mean, "std_dev": std, "z_score": z, "outlier_flag": z.abs() > threshold})


def exponential_smoothing(values: list[float], alpha: float) -> float:
    level = values[0] if values else 0.0
    for value in values[1:]:
        level = alpha * value + (1 - alpha) * level
    return float(level)


def holt_forecast(values: list[float], alpha: float, beta: float) -> tuple[float, float]:
    if len(values) < 2:
        return (values[0] if values else 0.0, 0.0)
    level = values[0]
    trend = values[1] - values[0]
    for value in values[1:]:
        prev_level = level
        level = alpha * value + (1 - alpha) * (level + trend)
        trend = beta * (level - prev_level) + (1 - beta) * trend
    return float(level + trend), float(trend)


def safety_stock(demand_std_dev: float, lead_time_days: float, service_level_z: float = 1.2816) -> float:
    return float(service_level_z * demand_std_dev * math.sqrt(max(lead_time_days, 0) / 30.0))
