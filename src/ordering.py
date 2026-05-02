"""Ordering logic for recommended order quantities."""

from __future__ import annotations

import math

import pandas as pd

from config import MINIMUM_ORDER_QTY, SAFETY_BUFFER_PERCENT


def compute_recommended_order(forecast_df: pd.DataFrame, stock_df: pd.DataFrame, forecast_date: pd.Timestamp) -> pd.DataFrame:
    result = forecast_df.copy()
    result["safety_buffer"] = result["predicted_demand"] * SAFETY_BUFFER_PERCENT

    if stock_df.empty:
        result["stock_on_hand"] = 0
        result["stock_on_order"] = 0
    else:
        latest_stock = (
            stock_df[stock_df["snapshot_date"] <= forecast_date]
            .sort_values(["part_number", "snapshot_date"])
            .groupby("part_number", as_index=False)
            .tail(1)[["part_number", "stock_on_hand", "stock_on_order"]]
        )
        result = result.merge(latest_stock, on="part_number", how="left")
        result[["stock_on_hand", "stock_on_order"]] = result[["stock_on_hand", "stock_on_order"]].fillna(0)

    raw = result["predicted_demand"] + result["safety_buffer"] - result["stock_on_hand"] - result["stock_on_order"]
    result["recommended_order"] = raw.apply(lambda x: max(0, math.ceil(x)))
    result.loc[(result["predicted_demand"] > 0) & (result["recommended_order"] == 0), "recommended_order"] = MINIMUM_ORDER_QTY
    return result
