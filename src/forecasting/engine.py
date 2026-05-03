from __future__ import annotations

import pandas as pd

from .calculations import exponential_smoothing
from ..inventory.logic import apply_order_constraints, demand_during_lead_time, reorder_point


def run_forecast(data: dict[str, pd.DataFrame], as_of_date: pd.Timestamp | None = None) -> pd.DataFrame:
    parts = data["parts"]
    usage = data["usage"]
    stock = data["stock_snapshots"]
    rows = []
    for p in parts.itertuples():
        hist = usage[usage["part_id"] == p.part_id].sort_values("week_start_date")
        vals = hist["usage_qty"].tolist() or [0.0]
        weekly = float(exponential_smoothing(vals, 0.4))
        lead_time_d = demand_during_lead_time(weekly, float(p.lead_time_days), period_days=7)
        ss = weekly * 0.5
        rop = reorder_point(lead_time_d, ss)
        st = stock[stock["part_id"] == p.part_id]
        soh = float(st["stock_on_hand"].iloc[-1]) if not st.empty else 0.0
        soo = float(st["stock_on_order"].iloc[-1]) if not st.empty else 0.0
        raw = max(0.0, rop - (soh + soo - lead_time_d))
        c = apply_order_constraints(raw, float(p.minimum_order_qty), float(p.order_multiple_qty))
        rows.append({
            "part_id": p.part_id,
            "forecast_demand": weekly,
            "lead_time_demand": lead_time_d,
            "safety_stock": ss,
            "reorder_point": rop,
            "stock_on_hand": soh,
            "stock_on_order": soo,
            "minimum_order_qty": float(p.minimum_order_qty),
            "order_multiple_qty": float(p.order_multiple_qty),
            "demand_source": "usage_only",
            "risk_level": "high" if raw > 0 else "low",
            "explanation": "usage_qty only demand; reorder based on ROP",
            **c,
        })
    return pd.DataFrame(rows)
