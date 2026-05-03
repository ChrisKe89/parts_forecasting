from __future__ import annotations

import math
import uuid
import pandas as pd

from .forecasting.engine import run_forecast
from .inventory.logic import apply_order_constraints


def _train_test_dates(usage: pd.DataFrame, train_months: int = 18, test_months: int = 6) -> tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp, pd.Timestamp]:
    test_end = usage["week_start_date"].max()
    test_start = test_end - pd.DateOffset(months=test_months) + pd.DateOffset(days=1)
    train_start = test_start - pd.DateOffset(months=train_months)
    train_end = test_start - pd.DateOffset(days=1)
    return train_start, train_end, test_start, test_end


def _simulate(data: dict[str, pd.DataFrame], forecast: pd.DataFrame, test_usage: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
    stock = data["stock_snapshots"].sort_values("snapshot_date").groupby("part_id", as_index=False).last()
    parts = data["parts"].copy()
    parts = parts.merge(forecast[["part_id", "forecast_demand", "lead_time_demand", "safety_stock", "reorder_point"]], on="part_id", how="left")
    open_orders: list[dict] = []
    weekly_rows: list[dict] = []
    metrics = {"orders": 0, "partial": 0, "delayed": 0, "cancelled": 0.0, "moq": 0, "mult": 0}

    stock_state = {r.part_id: {"on_hand": float(r.stock_on_hand), "backorder": 0.0} for r in stock.itertuples()}
    weeks = sorted(test_usage["week_start_date"].unique().tolist())

    for week in weeks:
        week_usage = test_usage[test_usage["week_start_date"] == week]
        for p in parts.itertuples():
            pid = p.part_id
            state = stock_state.setdefault(pid, {"on_hand": 0.0, "backorder": 0.0})
            opening = state["on_hand"]
            receipts = 0.0
            partial_receipts = 0.0
            stock_on_order = 0.0
            for o in open_orders:
                if o["part_id"] != pid:
                    continue
                if o["expected_arrival_date"] <= week and o["remaining_qty"] > 0:
                    rec = max(1.0, o["remaining_qty"] * 0.6) if o["remaining_qty"] > 1 else o["remaining_qty"]
                    rec = min(rec, o["remaining_qty"])
                    o["received_qty"] += rec
                    o["remaining_qty"] -= rec
                    receipts += rec
                    if o["remaining_qty"] > 0:
                        partial_receipts += rec
                        o["receipt_status"] = "partial"
                        o["expected_arrival_date"] = week + pd.Timedelta(days=7)
                        metrics["partial"] += 1
                        metrics["delayed"] += 1
                    else:
                        o["receipt_status"] = "full"
                if o["remaining_qty"] > 0:
                    stock_on_order += o["remaining_qty"]
            state["on_hand"] += receipts

            usage_qty = float(week_usage[week_usage["part_id"] == pid]["usage_qty"].sum())
            demand = usage_qty + state["backorder"]
            fulfilled = min(state["on_hand"], demand)
            unfulfilled = demand - fulfilled
            state["on_hand"] -= fulfilled
            state["backorder"] = unfulfilled

            projected = state["on_hand"] + stock_on_order - float(getattr(p, "lead_time_demand", 0.0))
            raw = max(0.0, float(getattr(p, "reorder_point", 0.0)) - projected)
            constraints = apply_order_constraints(raw, float(p.minimum_order_qty), float(p.order_multiple_qty))
            if constraints["final_order_qty"] > 0:
                metrics["orders"] += 1
                metrics["moq"] += int(constraints["moq_applied"])
                metrics["mult"] += int(constraints["order_multiple_applied"])
                open_orders.append({
                    "supplier_order_id": f"SIM-{len(open_orders)+1}", "part_id": pid, "order_date": week,
                    "original_order_qty": constraints["final_order_qty"], "received_qty": 0.0,
                    "remaining_qty": constraints["final_order_qty"],
                    "expected_arrival_date": week + pd.Timedelta(days=int(p.lead_time_days)),
                    "actual_arrival_date": pd.NaT, "receipt_status": "open",
                })
            weekly_rows.append({
                "part_id": pid, "week_start_date": week, "opening_stock": opening, "receipts_qty": receipts,
                "partial_receipts_qty": partial_receipts, "usage_qty": usage_qty, "fulfilled_qty": fulfilled,
                "unfulfilled_qty": unfulfilled, "backorder_qty": state["backorder"], "stock_on_order": stock_on_order,
                **constraints, "minimum_order_qty": float(p.minimum_order_qty), "order_multiple_qty": float(p.order_multiple_qty),
                "expected_arrival_date": week + pd.Timedelta(days=int(p.lead_time_days)), "closing_stock": state["on_hand"],
            })
    metrics["remaining_open"] = float(sum(o["remaining_qty"] for o in open_orders))
    return pd.DataFrame(weekly_rows), metrics


def run_backtest(data: dict[str, pd.DataFrame], enforce_fail_conditions: bool = True) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    usage = data["usage"].copy()
    usage["demand_source"] = "usage_only"
    train_start, train_end, test_start, test_end = _train_test_dates(usage)
    train_usage = usage[(usage.week_start_date >= train_start) & (usage.week_start_date <= train_end)]
    test_usage = usage[(usage.week_start_date >= test_start) & (usage.week_start_date <= test_end)]
    forecast = run_forecast({**data, "usage": train_usage})
    weekly, sim_metrics = _simulate(data, forecast, test_usage)

    true_demand = float(test_usage["usage_qty"].sum())
    fulfilled = float(weekly["fulfilled_qty"].sum())
    unfulfilled = float(weekly["unfulfilled_qty"].sum())
    model_service_level = fulfilled / true_demand if true_demand else 0.0
    baseline_service_level = float(data.get("baseline_service_level", 0.60))

    predicted_demand = float(forecast["forecast_demand"].sum() * max(1, len(test_usage["week_start_date"].unique())))
    mae = abs(predicted_demand - true_demand) / max(1.0, len(forecast))
    rmse = math.sqrt(((predicted_demand - true_demand) ** 2) / max(1.0, len(forecast)))

    summary = pd.DataFrame([{
        "run_id": str(uuid.uuid4()), "data_source": data.get("data_source", "synthetic"),
        "train_start_date": train_start, "train_end_date": train_end, "test_start_date": test_start, "test_end_date": test_end,
        "total_parts_generated": int(data["parts"]["part_id"].nunique()), "total_parts_evaluated": int(weekly["part_id"].nunique()),
        "total_models_generated": int(data["machine_models"]["model_id"].nunique()), "total_models_evaluated": int(test_usage["model_id"].nunique()),
        "actual_or_baseline_service_level": baseline_service_level, "model_service_level": model_service_level,
        "service_level_improvement": model_service_level - baseline_service_level, "baseline_fill_rate": baseline_service_level,
        "model_fill_rate": model_service_level, "stockout_reduction": 0.0, "baseline_stockout_count": 0,
        "model_stockout_count": int((weekly["unfulfilled_qty"] > 0).sum()), "true_demand": true_demand,
        "predicted_demand": predicted_demand, "fulfilled_qty": fulfilled, "unfulfilled_qty": unfulfilled,
        "MAE": mae, "RMSE": rmse, "forecast_bias": predicted_demand - true_demand,
        "under_forecast_count": int(predicted_demand < true_demand), "over_forecast_count": int(predicted_demand > true_demand),
        "average_inventory_baseline": 0.0, "average_inventory_model": float(weekly["closing_stock"].mean()), "inventory_change": 0.0,
        "total_supplier_orders_created": sim_metrics["orders"], "total_partial_receipts": sim_metrics["partial"],
        "total_delayed_receipts": sim_metrics["delayed"], "total_moq_adjustments": sim_metrics["moq"],
        "total_order_multiple_adjustments": sim_metrics["mult"],
    }])

    concerns = {"concerns": []}
    if baseline_service_level < 0.55 or baseline_service_level > 0.65:
        concerns["concerns"].append({"type": "service_level", "severity": "high", "message": "synthetic baseline outside 55%-65%"})
    if enforce_fail_conditions and (data["parts"]["part_id"].nunique() < 1000 or data["machine_models"]["model_id"].nunique() < 50):
        raise ValueError("Synthetic generation below required thresholds")
    return summary, weekly, concerns
