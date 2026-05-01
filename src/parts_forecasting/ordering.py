from __future__ import annotations

import math

import pandas as pd

from parts_forecasting.config import BASE_BUFFER_PCT, MAX_VARIABILITY_BUFFER_PCT, MINIMUM_ORDER_QTY, VARIABILITY_BUFFER_MULTIPLIER


def compute_recommended_order(forecast_df: pd.DataFrame, stock_df: pd.DataFrame, forecast_date: pd.Timestamp) -> pd.DataFrame:
    result = forecast_df.copy()

    if stock_df.empty:
        result["stock_on_hand"] = 0
        result["stock_on_order"] = 0
        result["stock_snapshot_date_used"] = pd.NaT
        result["forecast_reason"] = result["forecast_reason"].astype(str) + " | no prior stock snapshot"
    else:
        latest_stock = (
            stock_df[stock_df["snapshot_date"] <= forecast_date]
            .sort_values(["part_number", "snapshot_date"])
            .groupby("part_number", as_index=False)
            .tail(1)[["part_number", "stock_on_hand", "stock_on_order", "snapshot_date"]]
            .rename(columns={"snapshot_date": "stock_snapshot_date_used"})
        )
        result = result.merge(latest_stock, on="part_number", how="left")
        result[["stock_on_hand", "stock_on_order"]] = result[["stock_on_hand", "stock_on_order"]].fillna(0)
        no_snap = result["stock_snapshot_date_used"].isna()
        result.loc[no_snap, "forecast_reason"] = result.loc[no_snap, "forecast_reason"].astype(str) + " | no prior stock snapshot"

    result["current_stock_used"] = result["stock_on_hand"] + result["stock_on_order"]
    result["variability_buffer_pct"] = (result["coefficient_of_variation"] * VARIABILITY_BUFFER_MULTIPLIER).clip(upper=MAX_VARIABILITY_BUFFER_PCT)
    result["total_buffer_pct"] = BASE_BUFFER_PCT + result["variability_buffer_pct"]
    result["safety_buffer"] = result["adjusted_predicted_demand"] * result["total_buffer_pct"]

    raw = result["adjusted_predicted_demand"] + result["safety_buffer"] - result["current_stock_used"]
    result["recommended_order"] = raw.apply(lambda x: max(0, math.ceil(x)))
    result.loc[(result["adjusted_predicted_demand"] > 0) & (result["recommended_order"] == 0), "recommended_order"] = MINIMUM_ORDER_QTY
    return result
