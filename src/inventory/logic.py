from __future__ import annotations

import pandas as pd


def demand_during_lead_time(forecast: float, lead_time_days: float) -> float:
    return float(forecast * (lead_time_days / 30.0))


def reorder_point(demand_lt: float, safety_stock: float) -> float:
    return float(demand_lt + safety_stock)


def rolling_projected_stock(stock_df: pd.DataFrame, as_of_date: pd.Timestamp, lead_time_days: int, weekly_demand: float) -> float:
    latest = stock_df.loc[stock_df["snapshot_date"] <= as_of_date].sort_values("snapshot_date").tail(1)
    if latest.empty:
        return 0.0
    on_hand = float(latest.iloc[0]["stock_on_hand"])
    inbound = stock_df[(stock_df["expected_arrival_date"] <= as_of_date + pd.Timedelta(days=lead_time_days))]["stock_on_order"].sum()
    demand = weekly_demand * (lead_time_days / 7.0)
    return float(on_hand + inbound - demand)


def apply_moq(required_qty: float, minimum_order_quantity: float) -> float:
    if required_qty <= 0:
        return 0.0
    return float(max(required_qty, minimum_order_quantity))
