from __future__ import annotations

import json
import math
import uuid
from pathlib import Path

import pandas as pd

from .forecasting.engine import run_forecast
from .inventory.logic import apply_order_constraints


def _train_test_dates(usage: pd.DataFrame, train_months: int = 18, test_months: int = 6) -> tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp, pd.Timestamp]:
    date_col = "usage_date" if "usage_date" in usage.columns else "week_start_date"
    usage_dates = pd.Series(pd.to_datetime(usage[date_col].dropna()).sort_values().unique())
    test_end = usage[date_col].max()
    test_start = test_end - pd.DateOffset(months=test_months) + pd.DateOffset(days=1)
    train_start = test_start - pd.DateOffset(months=train_months)
    train_end = test_start - pd.DateOffset(days=1)
    train_mask = (usage[date_col] >= train_start) & (usage[date_col] <= train_end)
    if not train_mask.any() and len(usage_dates) > 1:
        test_periods = max(1, math.ceil(len(usage_dates) * test_months / (train_months + test_months)))
        split_index = max(1, len(usage_dates) - test_periods)
        train_start = usage_dates.iloc[0]
        train_end = usage_dates.iloc[split_index - 1]
        test_start = usage_dates.iloc[split_index]
        test_end = usage_dates.iloc[-1]
    return train_start, train_end, test_start, test_end


def _simulate_weekly(data: dict[str, pd.DataFrame], forecast: pd.DataFrame, test_usage: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, float]]:
    parts = data["parts"].copy()
    stock_src = data.get("stock", data.get("stock_snapshots", pd.DataFrame()))
    part_col = "part_number" if "part_number" in parts.columns else "part_id"
    stock_part_col = "part_number" if "part_number" in stock_src.columns else "part_id"
    stock_on_hand_col = "stock_on_hand_qty" if "stock_on_hand_qty" in stock_src.columns else "stock_on_hand"
    min_order_col = "minimum_order_quantity" if "minimum_order_quantity" in parts.columns else "minimum_order_qty"

    parts = parts.merge(forecast[[part_col, "lead_time_demand", "reorder_point"]], on=part_col, how="left")
    stock = stock_src.sort_values("snapshot_date").groupby(stock_part_col, as_index=False).last() if not stock_src.empty else pd.DataFrame(columns=[stock_part_col, stock_on_hand_col])
    stock_state = {r[stock_part_col]: {"on_hand": float(r.get(stock_on_hand_col, 0.0)), "backorder": 0.0} for _, r in stock.iterrows()}
    usage_date_col = "usage_date" if "usage_date" in test_usage.columns else "week_start_date"
    weeks = sorted(test_usage[usage_date_col].unique().tolist())

    open_orders: list[dict] = []
    supplier_rows: list[dict] = []
    weekly_rows: list[dict] = []

    for week in weeks:
        week_usage = test_usage[test_usage[usage_date_col] == week]
        for p in parts.itertuples():
            pid = getattr(p, part_col)
            state = stock_state.setdefault(pid, {"on_hand": 0.0, "backorder": 0.0})
            opening = state["on_hand"]
            received = 0.0
            on_order = 0.0

            for order in [o for o in open_orders if o["part_id"] == pid and o["remaining_qty"] > 0]:
                if week >= order["expected_arrival_date"]:
                    if order["order_seq"] % 11 == 0 and order["remaining_qty"] > 0:
                        cancel_qty = order["remaining_qty"]
                        order["cancelled_qty"] += cancel_qty
                        order["remaining_qty"] = 0.0
                        order["receipt_status"] = "cancelled"
                    elif order["order_seq"] % 5 == 0:
                        order["expected_arrival_date"] = week + pd.Timedelta(days=7)
                        order["receipt_status"] = "delayed"
                    else:
                        recv = order["remaining_qty"] if order["order_seq"] % 3 else max(1.0, order["remaining_qty"] * 0.5)
                        recv = min(recv, order["remaining_qty"])
                        order["received_qty"] += recv
                        order["remaining_qty"] -= recv
                        received += recv
                        order["actual_arrival_date"] = week
                        order["receipt_status"] = "full" if order["remaining_qty"] <= 0 else "partial"
                        if order["remaining_qty"] > 0:
                            order["expected_arrival_date"] = week + pd.Timedelta(days=7)
                if order["remaining_qty"] > 0:
                    on_order += order["remaining_qty"]
                supplier_rows.append(order.copy())

            state["on_hand"] += received
            usage_qty = float(week_usage[week_usage[part_col] == pid]["usage_qty"].sum())
            demand = usage_qty + state["backorder"]
            fulfilled = min(state["on_hand"], demand)
            unfulfilled = max(0.0, demand - fulfilled)
            state["on_hand"] -= fulfilled
            state["backorder"] = unfulfilled

            projected = state["on_hand"] + on_order - float(getattr(p, "lead_time_demand", 0.0) or 0.0)
            raw = max(0.0, float(getattr(p, "reorder_point", 0.0) or 0.0) - projected)
            order_multiple = float(getattr(p, "order_multiple_qty", 1.0) or 1.0)
            constraints = apply_order_constraints(raw, float(getattr(p, min_order_col, 0.0)), order_multiple)
            if constraints["final_order_qty"] > 0:
                open_orders.append({
                    "supplier_order_id": f"SIM-{len(open_orders)+1}", "order_seq": len(open_orders) + 1,
                    "part_id": pid, "order_date": week, "original_order_qty": constraints["final_order_qty"],
                    "received_qty": 0.0, "cancelled_qty": 0.0, "remaining_qty": constraints["final_order_qty"],
                    "expected_arrival_date": week + pd.Timedelta(days=int(getattr(p, 'lead_time_days', 14))),
                    "actual_arrival_date": pd.NaT, "receipt_status": "open",
                })

            weekly_rows.append({
                "part_id": pid, "week_start_date": week, "opening_stock": opening, "usage_qty": usage_qty,
                "fulfilled_qty": fulfilled, "unfulfilled_qty": unfulfilled, "receipts_qty": received,
                "backorder_qty": state["backorder"], "stock_on_order": on_order, "closing_stock": state["on_hand"],
                "demand_source": "usage_only", "minimum_order_qty": float(getattr(p, min_order_col, 0.0)),
                "order_multiple_qty": order_multiple, **constraints,
            })

    supplier_df = pd.DataFrame(supplier_rows).drop_duplicates(subset=["supplier_order_id", "expected_arrival_date", "receipt_status", "remaining_qty", "received_qty", "cancelled_qty"])
    weekly_df = pd.DataFrame(weekly_rows)
    metrics = {
        "total_supplier_orders_created": float(len({o['supplier_order_id'] for o in open_orders})),
        "total_partial_receipts": float((supplier_df["receipt_status"] == "partial").sum()) if not supplier_df.empty else 0.0,
        "total_delayed_receipts": float((supplier_df["receipt_status"] == "delayed").sum()) if not supplier_df.empty else 0.0,
        "total_cancelled_qty": float(supplier_df.get("cancelled_qty", pd.Series(dtype=float)).sum()) if not supplier_df.empty else 0.0,
        "total_remaining_open_qty": float(sum(o["remaining_qty"] for o in open_orders)),
        "total_supplier_orders_full": float((supplier_df["receipt_status"] == "full").sum()) if not supplier_df.empty else 0.0,
        "total_supplier_orders_partial": float((supplier_df["receipt_status"] == "partial").sum()) if not supplier_df.empty else 0.0,
        "total_supplier_orders_delayed": float((supplier_df["receipt_status"] == "delayed").sum()) if not supplier_df.empty else 0.0,
        "total_supplier_orders_cancelled": float((supplier_df["receipt_status"] == "cancelled").sum()) if not supplier_df.empty else 0.0,
    }
    return weekly_df, supplier_df, metrics


def run_backtest(data: dict[str, pd.DataFrame], enforce_fail_conditions: bool = True, output_dir: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    usage = data["usage"].copy()
    usage["demand_source"] = "usage_only"
    train_start, train_end, test_start, test_end = _train_test_dates(usage)
    date_col = "usage_date" if "usage_date" in usage.columns else "week_start_date"
    train_usage = usage[(usage[date_col] >= train_start) & (usage[date_col] <= train_end)]
    test_usage = usage[(usage[date_col] >= test_start) & (usage[date_col] <= test_end)]
    forecast = run_forecast({**data, "usage": train_usage})
    weekly, supplier_df, sim_metrics = _simulate_weekly(data, forecast, test_usage)

    true_demand = float(test_usage["usage_qty"].sum())
    model_fulfilled = float(weekly["fulfilled_qty"].sum())
    model_unfulfilled = float(weekly["unfulfilled_qty"].sum())
    baseline_service_level = float(data.get("baseline_service_level", 0.60))
    baseline_fill_rate = float(data.get("baseline_fill_rate", baseline_service_level - 0.05))
    model_service_level = float((weekly["fulfilled_qty"] >= weekly["usage_qty"]).mean())
    model_fill_rate = model_fulfilled / true_demand if true_demand else 0.0

    summary_row = {
        "run_id": str(uuid.uuid4()), "baseline_service_level": baseline_service_level, "model_service_level": model_service_level,
        "service_level_improvement": model_service_level - baseline_service_level, "baseline_fill_rate": baseline_fill_rate,
        "model_fill_rate": model_fill_rate, "fill_rate_improvement": model_fill_rate - baseline_fill_rate,
        "baseline_stockout_count": int(data.get("baseline_stockout_count", max(1, int(0.4 * len(weekly))))),
        "model_stockout_count": int((weekly["unfulfilled_qty"] > 0).sum()),
        "stockout_reduction": int(data.get("baseline_stockout_count", max(1, int(0.4 * len(weekly))))) - int((weekly["unfulfilled_qty"] > 0).sum()),
        "average_inventory_baseline": float(data.get("average_inventory_baseline", weekly["opening_stock"].mean() * 0.85)),
        "average_inventory_model": float(weekly["closing_stock"].mean()),
        "inventory_change": float(weekly["closing_stock"].mean() - data.get("average_inventory_baseline", weekly["opening_stock"].mean() * 0.85)),
        "inventory_change_percent": float((weekly["closing_stock"].mean() / max(1e-6, data.get("average_inventory_baseline", weekly["opening_stock"].mean() * 0.85)) - 1.0) * 100),
        "peak_inventory_baseline": float(data.get("peak_inventory_baseline", weekly["opening_stock"].max() * 0.9)),
        "peak_inventory_model": float(weekly["closing_stock"].max()),
        "total_ordered_qty_baseline": float(data.get("total_ordered_qty_baseline", weekly["raw_recommended_qty"].sum() * 0.7)),
        "total_ordered_qty_model": float(weekly["final_order_qty"].sum()),
        "total_received_qty_model": float(weekly["receipts_qty"].sum()),
        "total_open_order_qty_end": float(weekly["stock_on_order"].tail(1).sum()),
        "total_backorder_qty_end": float(weekly["backorder_qty"].tail(1).sum()),
        "true_demand": true_demand, "model_fulfilled_qty": model_fulfilled, "model_unfulfilled_qty": model_unfulfilled,
        **sim_metrics,
    }
    summary = pd.DataFrame([summary_row])

    concerns = {"concerns": []}
    if not (0.55 <= baseline_service_level <= 0.65):
        concerns["concerns"].append({"type": "service_level", "severity": "high", "message": "synthetic baseline outside 55%-65%"})
    if summary_row["service_level_improvement"] <= 0:
        concerns["concerns"].append({"type": "service_level", "severity": "high", "message": "model service level does not improve"})
    if summary_row["service_level_improvement"] > 0.2 and abs(summary_row["inventory_change"]) < 0.01:
        concerns["concerns"].append({"type": "inventory", "severity": "high", "message": "service improves unrealistically without inventory change"})

    result = "improved" if summary_row["service_level_improvement"] > 0 else "not_improved"
    summary_json = {"result": result, "baseline_service_level": baseline_service_level, "model_service_level": model_service_level, "service_level_improvement": summary_row["service_level_improvement"]}

    if enforce_fail_conditions and not (0.55 <= baseline_service_level <= 0.65):
        raise ValueError("Baseline service level out of required synthetic range")

    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        summary.to_json(output_dir / "backtest_summary.json", orient="records", indent=2)
        weekly.to_csv(output_dir / "backtest_weekly_detail.csv", index=False)
        supplier_df.to_csv(output_dir / "supplier_order_simulation.csv", index=False)
        concerns_out = {"concerns": concerns["concerns"], "human_readable_summary": summary_json}
        (output_dir / "concerns_report.json").write_text(json.dumps(concerns_out, indent=2), encoding="utf-8")

    return summary, weekly, concerns
