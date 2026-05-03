from __future__ import annotations

import pandas as pd

from .calculations import (
    exponential_smoothing,
    holt_forecast,
    safety_stock,
    service_level_to_z,
    usage_per_machine,
    zscore_outliers,
)
from ..inventory.logic import apply_moq, demand_during_lead_time, reorder_point
from ..utils.config import ForecastingConfig, DEFAULT_CONFIG


def _pipeline_supply_qty(stock_rows: pd.DataFrame, target_date: pd.Timestamp) -> float:
    if stock_rows.empty:
        return 0.0
    arrivals = stock_rows[stock_rows["expected_arrival_date"] <= target_date]
    return float(arrivals["open_purchase_order_qty"].sum())


def run_forecast(data: dict[str, pd.DataFrame], config: ForecastingConfig = DEFAULT_CONFIG, as_of_date: pd.Timestamp | None = None) -> pd.DataFrame:
    parts, usage, installs, stock = data["parts"], data["usage"], data["installs"], data["stock"]
    as_of = as_of_date or usage["usage_date"].max()
    usage_rates = usage_per_machine(usage)
    rows = []

    for pid, part_rows in parts.groupby("part_number", sort=True):
        group = part_rows["smoothing_group"].iloc[0]
        alpha = config.smoothing_groups.get(group, config.smoothing_groups["C"])
        models = part_rows["model"].dropna().unique().tolist()

        model_bases = []
        model_methods = []
        model_std_terms = []
        outlier_count = 0
        sparse_history = False
        install_adjustment_available = False
        scheduled_demand = 0.0
        projected_demand = 0.0

        for model in models:
            hist = usage[(usage["part_number"] == pid) & (usage["model"] == model)].sort_values("usage_date")
            vals = hist["usage_qty"].tolist()
            zinfo = zscore_outliers(hist["usage_qty"], config.z_threshold) if not hist.empty else pd.DataFrame({"outlier_flag": []})
            adjusted_vals = vals
            if not hist.empty:
                median_usage = float(hist["usage_qty"].median())
                adjusted_vals = [median_usage if flag else float(v) for v, flag in zip(vals, zinfo["outlier_flag"].tolist())]

            if len(vals) >= config.minimum_history_points_for_holt:
                hforecast, trend = holt_forecast(adjusted_vals, alpha, config.beta)
                trend_ratio = abs(trend) / max(abs(hforecast), 1.0)
                if trend_ratio >= config.trend_significance_threshold:
                    base, method = hforecast, "holt"
                else:
                    base, method = exponential_smoothing(adjusted_vals or [0.0], alpha), "exponential_smoothing"
            else:
                base, method = exponential_smoothing(adjusted_vals or [0.0], alpha), "exponential_smoothing"
                sparse_history = True

            upr = usage_rates[(usage_rates.part_number == pid) & (usage_rates.model == model)]
            usage_pm = float(upr["usage_per_machine"].iloc[0]) if not upr.empty else 0.0
            ins = installs[(installs.part_number == pid) & (installs.model == model)]
            install_adjustment_available = install_adjustment_available or (not ins.empty)
            scheduled_installs = ins[(ins.install_status == "scheduled") & (ins.install_date > as_of)]
            projected_installs = ins[(ins.install_status == "projected") & (ins.install_date > as_of)]
            scheduled_demand += float(scheduled_installs["install_qty"].sum() * usage_pm)
            projected_demand += float((projected_installs["install_qty"] * projected_installs["projected_install_confidence"]).sum() * usage_pm)

            model_bases.append(float(base))
            model_methods.append(method)
            model_std_terms.extend(adjusted_vals)
            outlier_count += int(zinfo["outlier_flag"].sum()) if not hist.empty else 0

        base_demand = float(sum(model_bases))
        final_demand_weekly = float(base_demand + scheduled_demand + projected_demand)
        lead_time_days = float(part_rows["lead_time_days"].iloc[0] or config.lead_time_days_default)

        demand_std = float(pd.Series(model_std_terms).std(ddof=0)) if len(model_std_terms) >= 2 else 0.0
        z_value = service_level_to_z(config.service_level_target)
        ss = safety_stock(demand_std, lead_time_days / 7.0, z_value)
        dlt = demand_during_lead_time(final_demand_weekly, lead_time_days, period_days=7)
        rop = reorder_point(dlt, ss)

        stock_rows = stock[stock.part_number == pid]
        stock_on_hand_qty = float(stock_rows["stock_on_hand_qty"].max()) if not stock_rows.empty else 0.0
        allocated_qty = float(stock_rows["allocated_qty"].max()) if not stock_rows.empty else 0.0
        backorder_qty = float(stock_rows["unfulfilled_qty"].max()) if not stock_rows.empty else 0.0
        effective_stock_qty = float(stock_on_hand_qty - allocated_qty - backorder_qty)

        arrival_date = as_of + pd.Timedelta(days=int(lead_time_days))
        pipeline_supply_qty = _pipeline_supply_qty(stock_rows, arrival_date)
        projected_stock = float(effective_stock_qty + pipeline_supply_qty - dlt)
        reorder_triggered = projected_stock < rop

        target_stock = rop + final_demand_weekly
        required_qty = max(0.0, target_stock - projected_stock)
        moq = float(part_rows["minimum_order_quantity"].iloc[0] or config.moq_default)
        final_order_qty, moq_applied = apply_moq(required_qty, moq, reorder_triggered)

        method = "holt" if "holt" in model_methods else "exponential_smoothing"
        risk = "stockout risk before arrival" if projected_stock < 0 else "pipeline supply sufficient"
        if reorder_triggered:
            explanation = (
                f"Order recommended because projected stock of {projected_stock:.2f} is below reorder point of {rop:.2f}. "
                f"Lead-time demand is {dlt:.2f} and safety stock is {ss:.2f} at {config.service_level_target:.0%} service level. "
                + (f"MOQ increased the order from {required_qty:.2f} to {final_order_qty:.2f}." if moq_applied else "MOQ did not change the required order quantity.")
            )
        else:
            explanation = (
                f"No order recommended because projected stock of {projected_stock:.2f} is above reorder point of {rop:.2f}. "
                f"Current pipeline supply of {pipeline_supply_qty:.2f} is sufficient for the lead-time window."
            )

        rows.append({
            "part_number": pid,
            "forecast_method_used": method,
            "base_forecast": base_demand,
            "weekly_demand_rate": final_demand_weekly,
            "lead_time_demand": dlt,
            "demand_std_dev": demand_std,
            "service_level_target": config.service_level_target,
            "z_score": z_value,
            "safety_stock": ss,
            "stock_on_hand_qty": stock_on_hand_qty,
            "allocated_qty": allocated_qty,
            "backorder_qty": backorder_qty,
            "effective_stock_qty": effective_stock_qty,
            "pipeline_supply_qty": pipeline_supply_qty,
            "projected_stock": projected_stock,
            "reorder_point": rop,
            "reorder_triggered": bool(reorder_triggered),
            "minimum_order_quantity": moq,
            "required_quantity": required_qty,
            "final_order_quantity": final_order_qty,
            "moq_adjustment_applied": bool(moq_applied),
            "scheduled_install_demand": scheduled_demand,
            "projected_install_demand": projected_demand,
            "final_adjusted_demand": final_demand_weekly,
            "ordering_date": as_of,
            "arrival_date": arrival_date,
            "forecasted_demand_covered": dlt,
            "projected_stock_at_arrival": projected_stock,
            "stockout_risk_before_arrival": bool(projected_stock < 0),
            "outlier_count": outlier_count,
            "trend_note": "trend significant" if method == "holt" else "trend not significant",
            "install_adjustment_available": install_adjustment_available,
            "sparse_history_fallback_applied": sparse_history,
            "recommendation_explanation": explanation,
            "main_risk": risk,
        })
    return pd.DataFrame(rows)
