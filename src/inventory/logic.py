from __future__ import annotations

import math
import pandas as pd


def demand_during_lead_time(forecast_per_period: float, lead_time_days: float, period_days: int = 7) -> float:
    lead_time_periods = max(lead_time_days, 0) / period_days
    return float(forecast_per_period * lead_time_periods)


def reorder_point(demand_lt: float, safety_stock: float) -> float:
    return float(demand_lt + safety_stock)


def apply_moq(required_qty: float, minimum_order_quantity: float, reorder_triggered: bool) -> tuple[float, bool]:
    if (not reorder_triggered) or required_qty <= 0:
        return 0.0, False
    final_qty = max(required_qty, minimum_order_quantity)
    return float(final_qty), bool(final_qty > required_qty)


def apply_order_constraints(raw_recommended_qty: float, minimum_order_qty: float, order_multiple_qty: float) -> dict[str, float | bool]:
    if raw_recommended_qty <= 0:
        return {
            "raw_recommended_qty": 0.0,
            "final_order_qty": 0.0,
            "moq_applied": False,
            "order_multiple_applied": False,
        }
    final_qty = float(raw_recommended_qty)
    moq_applied = False
    multiple_applied = False
    if minimum_order_qty > 0 and final_qty < minimum_order_qty:
        final_qty = float(minimum_order_qty)
        moq_applied = True
    if order_multiple_qty and order_multiple_qty > 1:
        rounded = math.ceil(final_qty / order_multiple_qty) * order_multiple_qty
        multiple_applied = rounded != final_qty
        final_qty = float(rounded)
    return {
        "raw_recommended_qty": float(raw_recommended_qty),
        "final_order_qty": float(final_qty),
        "moq_applied": bool(moq_applied),
        "order_multiple_applied": bool(multiple_applied),
    }


def rolling_ordering_simulation(
    on_hand: float,
    weekly_demand: float,
    lead_time_days: int,
    incoming_orders: pd.DataFrame,
    ordering_date: pd.Timestamp,
) -> dict[str, float | str | bool | pd.Timestamp]:
    arrival_date = ordering_date + pd.Timedelta(days=lead_time_days)
    weeks_to_arrival = max(1, math.ceil(lead_time_days / 7))
    horizon_demand = weekly_demand * weeks_to_arrival
    inbound_before_arrival = 0.0
    if not incoming_orders.empty:
        inbound_before_arrival = float(
            incoming_orders[incoming_orders["expected_arrival_date"] <= arrival_date]["stock_on_order"].sum()
        )
    projected_stock_at_arrival = float(on_hand + inbound_before_arrival - horizon_demand)
    stockout_risk_before_arrival = projected_stock_at_arrival < 0
    return {
        "ordering_date": ordering_date,
        "arrival_date": arrival_date,
        "forecasted_demand_covered": float(horizon_demand),
        "projected_stock_at_arrival": projected_stock_at_arrival,
        "stockout_risk_before_arrival": bool(stockout_risk_before_arrival),
    }
