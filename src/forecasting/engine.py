from __future__ import annotations

import pandas as pd

from forecasting.calculations import exponential_smoothing, holt_forecast, safety_stock, usage_per_machine, zscore_outliers
from inventory.logic import apply_moq, demand_during_lead_time, reorder_point, rolling_projected_stock
from utils.config import ForecastingConfig, DEFAULT_CONFIG


def run_forecast(data: dict[str, pd.DataFrame], config: ForecastingConfig = DEFAULT_CONFIG, as_of_date: pd.Timestamp | None = None) -> pd.DataFrame:
    parts, usage, installs, stock = data["parts"], data["usage"], data["installs"], data["stock"]
    as_of = as_of_date or usage["usage_date"].max()
    usage_rates = usage_per_machine(usage)
    rows = []
    for _, part in parts.iterrows():
        pid, model, group = part["part_id"], part["model"], part["smoothing_group"]
        alpha = config.smoothing_groups.get(group, config.smoothing_groups["C"])
        hist = usage[(usage["part_id"] == pid) & (usage["model"] == model)].sort_values("usage_date")
        vals = hist["usage_qty"].tolist()
        zinfo = zscore_outliers(hist["usage_qty"], config.z_threshold) if not hist.empty else pd.DataFrame({"z_score": [0], "outlier_flag": [False], "std_dev": [0]})
        if len(vals) >= config.minimum_history_points_for_holt:
            hforecast, trend = holt_forecast(vals, alpha, config.beta)
            base, method = hforecast, "holt"
        else:
            base, trend, method = exponential_smoothing(vals or [0.0], alpha), 0.0, "exponential_smoothing"
        upr = usage_rates[(usage_rates.part_id == pid) & (usage_rates.model == model)]
        usage_pm = float(upr["usage_per_machine"].iloc[0]) if not upr.empty else 0.0
        ins = installs[(installs.part_id == pid) & (installs.model == model)]
        scheduled = ins[(ins.install_status == "scheduled") & (ins.install_date > as_of)]["install_qty"].sum() * usage_pm
        projected = (ins[(ins.install_status == "projected") & (ins.install_date > as_of)]["install_qty"] * ins[(ins.install_status == "projected") & (ins.install_date > as_of)]["projected_install_confidence"]).sum() * usage_pm
        adj = float(base + scheduled + projected)
        lead = float(part.get("lead_time_days", config.lead_time_days_default) or config.lead_time_days_default)
        demand_std = float(zinfo["std_dev"].iloc[0]) if "std_dev" in zinfo else 0.0
        ss = safety_stock(demand_std, lead)
        dlt = demand_during_lead_time(adj, lead)
        rop = reorder_point(dlt, ss)
        pstock_df = stock[(stock.part_id == pid) & (stock.model == model)]
        pstock = rolling_projected_stock(pstock_df, as_of, int(lead + config.lead_time_buffer_days), weekly_demand=adj / 4.0)
        target_stock = rop + adj
        req = target_stock - pstock
        moq = float(part.get("minimum_order_quantity", config.moq_default) or config.moq_default)
        rec = apply_moq(req, moq)
        triggered = pstock < rop
        rows.append({
            "part_id": pid, "model": model, "smoothing_group": group, "forecast_method_used": method,
            "base_forecast_demand": base, "trend_value": trend, "trend_direction": "up" if trend > 0 else ("down" if trend < 0 else "flat"),
            "usage_per_machine": usage_pm, "scheduled_install_demand": scheduled, "projected_install_demand": projected,
            "install_adjusted_forecast": adj, "demand_std_dev": demand_std, "z_score_max": float(zinfo["z_score"].abs().max()),
            "outlier_count": int(zinfo["outlier_flag"].sum()), "safety_stock": ss, "demand_during_lead_time": dlt,
            "reorder_point": rop, "stock_on_hand": float(pstock_df["stock_on_hand"].max()) if not pstock_df.empty else 0.0,
            "stock_on_order": float(pstock_df["stock_on_order"].sum()) if not pstock_df.empty else 0.0, "projected_stock": pstock,
            "minimum_order_quantity": moq, "order_triggered": bool(triggered), "recommended_order_qty": rec if triggered else 0.0,
            "stockout_risk": "high" if triggered else "low", "service_level_target": config.service_level_target,
            "confidence_score": max(0.0, min(1.0, 1.0 - (demand_std / (adj + 1e-6))))
        })
    return pd.DataFrame(rows)
