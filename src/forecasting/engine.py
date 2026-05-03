from __future__ import annotations

import pandas as pd

from .calculations import exponential_smoothing
from ..inventory.logic import apply_order_constraints, demand_during_lead_time, reorder_point


def run_forecast(data: dict[str, pd.DataFrame], as_of_date: pd.Timestamp | None = None) -> pd.DataFrame:
    parts = data["parts"]
    usage = data["usage"]
    stock = data.get("stock", data.get("stock_snapshots", pd.DataFrame()))
    part_col = "part_number" if "part_number" in parts.columns else "part_id"
    usage_date_col = "usage_date" if "usage_date" in usage.columns else "week_start_date"
    stock_on_hand_col = "stock_on_hand_qty" if "stock_on_hand_qty" in stock.columns else "stock_on_hand"
    stock_on_order_col = "open_purchase_order_qty" if "open_purchase_order_qty" in stock.columns else "stock_on_order"
    min_order_col = "minimum_order_quantity" if "minimum_order_quantity" in parts.columns else "minimum_order_qty"
    order_multiple_col = "order_multiple_qty" if "order_multiple_qty" in parts.columns else None
    rows = []
    for p in parts.itertuples():
        part_value = getattr(p, part_col)
        hist = usage[usage[part_col] == part_value].sort_values(usage_date_col)
        vals = hist["usage_qty"].tolist() or [0.0]
        weekly = float(exponential_smoothing(vals, 0.4))
        lead_time_d = demand_during_lead_time(weekly, float(p.lead_time_days), period_days=7)
        ss = weekly * 0.5
        rop = reorder_point(lead_time_d, ss)
        st = stock[stock[part_col] == part_value] if not stock.empty else pd.DataFrame()
        soh = float(st[stock_on_hand_col].iloc[-1]) if not st.empty else 0.0
        soo = float(st[stock_on_order_col].iloc[-1]) if not st.empty else 0.0
        raw = max(0.0, rop - (soh + soo - lead_time_d))
        order_multiple = float(getattr(p, order_multiple_col)) if order_multiple_col else 1.0
        c = apply_order_constraints(raw, float(getattr(p, min_order_col)), order_multiple)
        rows.append({
            part_col: part_value,
            "forecast_demand": weekly,
            "lead_time_demand": lead_time_d,
            "safety_stock": ss,
            "reorder_point": rop,
            "stock_on_hand": soh,
            "stock_on_order": soo,
            "minimum_order_qty": float(getattr(p, min_order_col)),
            "order_multiple_qty": order_multiple,
            "demand_source": "usage_only",
            "risk_level": "high" if raw > 0 else "low",
            "explanation": "usage_qty only demand; reorder based on ROP",
            **c,
        })
    return pd.DataFrame(rows)
