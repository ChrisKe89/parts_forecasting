from __future__ import annotations

import pandas as pd

from forecasting.calculations import (
    exponential_smoothing,
    holt_forecast,
    safety_stock,
    service_level_to_z,
    usage_per_machine,
    zscore_outliers,
)
from inventory.logic import apply_moq, demand_during_lead_time, reorder_point, rolling_ordering_simulation
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
        install_unavailable = ins.empty
        scheduled_installs = ins[(ins.install_status == "scheduled") & (ins.install_date > as_of)]
        projected_installs = ins[(ins.install_status == "projected") & (ins.install_date > as_of)]
        scheduled_demand = float(scheduled_installs["install_qty"].sum() * usage_pm)
        projected_demand = float((projected_installs["install_qty"] * projected_installs["projected_install_confidence"]).sum() * usage_pm)
        final_demand_weekly = float(base + scheduled_demand + projected_demand)

        lead_time_days = float(part.get("lead_time_days", config.lead_time_days_default) or config.lead_time_days_default)
        lead_time_periods = lead_time_days / 7.0
        lead_time_start = as_of + pd.Timedelta(days=1)
        lead_time_end = as_of + pd.Timedelta(days=int(lead_time_days))

        demand_std = float(zinfo["std_dev"].iloc[0]) if len(vals) >= 2 else 0.0
        sparse_history = len(vals) < 6
        if sparse_history:
            demand_std = max(demand_std, abs(base) * 0.25)
        z_value = service_level_to_z(config.service_level_target)
        ss = safety_stock(demand_std, lead_time_periods, z_value)
        dlt = demand_during_lead_time(final_demand_weekly, lead_time_days, period_days=7)
        rop = reorder_point(dlt, ss)

        pstock_df = stock[(stock.part_id == pid) & (stock.model == model)]
        on_hand = float(pstock_df["stock_on_hand"].max()) if not pstock_df.empty else 0.0
        sim = rolling_ordering_simulation(on_hand, final_demand_weekly, int(lead_time_days), pstock_df, as_of)
        projected_stock = float(sim["projected_stock_at_arrival"])

        reorder_triggered = projected_stock < rop
        target_stock = rop + final_demand_weekly
        required_qty = max(0.0, target_stock - projected_stock)
        moq = float(part.get("minimum_order_quantity", config.moq_default) or config.moq_default)
        final_order_qty, moq_applied = apply_moq(required_qty, moq, reorder_triggered)
        reason = "Projected stock below reorder point" if reorder_triggered else "Projected stock meets reorder point"
        explanation = (
            f"Order {'recommended' if reorder_triggered else 'not recommended'} because projected stock of {projected_stock:.2f} "
            f"is {'below' if reorder_triggered else 'above'} reorder point of {rop:.2f}. "
            f"Lead-time demand is {dlt:.2f} and safety stock is {ss:.2f} at service level {config.service_level_target:.0%}. "
            f"MOQ {'increased' if moq_applied else 'did not change'} order from {required_qty:.2f} to {final_order_qty:.2f}."
        )

        rows.append({
            "part_id": pid,
            "model": model,
            "forecast_method_used": method,
            "base_forecast": float(base),
            "weekly_demand_rate": final_demand_weekly,
            "lead_time_demand": dlt,
            "lead_time_window_start": lead_time_start,
            "lead_time_window_end": lead_time_end,
            "demand_std_dev": demand_std,
            "service_level_target": config.service_level_target,
            "z_score": z_value,
            "safety_stock": ss,
            "projected_stock": projected_stock,
            "reorder_point": rop,
            "reorder_triggered": bool(reorder_triggered),
            "reorder_reason": reason,
            "minimum_order_quantity": moq,
            "required_quantity": required_qty,
            "final_order_quantity": final_order_qty,
            "moq_adjustment_applied": bool(moq_applied),
            "usage_per_machine": usage_pm,
            "scheduled_install_demand": scheduled_demand,
            "projected_install_demand": projected_demand,
            "confidence_factor": float(projected_installs["projected_install_confidence"].mean()) if not projected_installs.empty else 0.0,
            "final_adjusted_demand": final_demand_weekly,
            "install_adjustment_available": not install_unavailable,
            "ordering_date": sim["ordering_date"],
            "arrival_date": sim["arrival_date"],
            "forecasted_demand_covered": sim["forecasted_demand_covered"],
            "projected_stock_at_arrival": sim["projected_stock_at_arrival"],
            "stockout_risk_before_arrival": sim["stockout_risk_before_arrival"],
            "explanation": explanation,
            "outlier_count": int(zinfo["outlier_flag"].sum()),
            "trend_note": "trend significant" if abs(trend) >= config.trend_significance_threshold else "trend not significant",
            "sparse_history_fallback_applied": sparse_history,
        })
    return pd.DataFrame(rows)
