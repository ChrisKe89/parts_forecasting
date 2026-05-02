from __future__ import annotations

import math
from statistics import NormalDist
import pandas as pd


def usage_per_machine(usage_df: pd.DataFrame) -> pd.DataFrame:
    grouped = usage_df.groupby(["part_number", "model"], as_index=False).agg(
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


def service_level_to_z(service_level_target: float) -> float:
    lookup = {0.80:0.8416,0.85:1.0364,0.90:1.2816,0.95:1.6449,0.98:2.0537,0.99:2.3263}
    rounded = round(float(service_level_target), 2)
    if rounded in lookup:
        return lookup[rounded]
    bounded = min(0.9999, max(0.5001, float(service_level_target)))
    return float(NormalDist().inv_cdf(bounded))


def safety_stock(demand_std_dev: float, lead_time_periods: float, service_level_z: float) -> float:
    return float(service_level_z * demand_std_dev * math.sqrt(max(lead_time_periods, 0)))
