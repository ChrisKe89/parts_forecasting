import math

import pandas as pd

from src.backtesting import run_backtest


def test_known_outcome_service_level_regression(tmp_path):
    scenario_dir = tmp_path / "known_outcome_service_level"
    scenario_dir.mkdir(parents=True, exist_ok=True)

    parts_master = pd.DataFrame(
        [
            {
                "part_id": "P_SIMPLE",
                "part_description": "Simple constant demand part",
                "minimum_order_qty": 20,
                "order_multiple_qty": 10,
                "preferred_supplier_id": "S1",
                "lead_time_days": 14,
            },
            {
                "part_id": "P_PARTIAL",
                "part_description": "Partial receipt test part",
                "minimum_order_qty": 12,
                "order_multiple_qty": 4,
                "preferred_supplier_id": "S1",
                "lead_time_days": 14,
            },
        ]
    )

    models = pd.DataFrame([{"model_id": "M1", "model_description": "Controlled test model"}])

    weeks = pd.date_range("2026-01-05", periods=24, freq="W-MON")
    usage = pd.DataFrame(
        [
            {
                "part_id": part_id,
                "model_id": "M1",
                "week_start_date": week,
                "usage_qty": qty,
            }
            for week in weeks
            for part_id, qty in (("P_SIMPLE", 10), ("P_PARTIAL", 8))
        ]
    )

    stock_snapshots = pd.DataFrame(
        [
            {"part_id": "P_SIMPLE", "snapshot_date": "2026-05-04", "stock_on_hand": 20, "stock_on_order": 0, "allocated_qty": 0},
            {"part_id": "P_PARTIAL", "snapshot_date": "2026-05-04", "stock_on_hand": 8, "stock_on_order": 0, "allocated_qty": 0},
        ]
    )

    tech_orders = pd.DataFrame(
        [
            {"part_id": "P_SIMPLE", "model_id": "M1", "order_date": "2026-05-04", "tech_order_qty": 10, "fulfilled_qty": 10, "unfulfilled_qty": 0},
            {"part_id": "P_PARTIAL", "model_id": "M1", "order_date": "2026-05-04", "tech_order_qty": 8, "fulfilled_qty": 8, "unfulfilled_qty": 0},
        ]
    )

    # Store each CSV in its own scenario folder for reproducibility/debugging.
    parts_master.to_csv(scenario_dir / "parts_master.csv", index=False)
    models.to_csv(scenario_dir / "models.csv", index=False)
    usage.to_csv(scenario_dir / "usage.csv", index=False)
    stock_snapshots.to_csv(scenario_dir / "stock_snapshots.csv", index=False)
    tech_orders.to_csv(scenario_dir / "tech_orders.csv", index=False)

    data = {
        "parts": parts_master,
        "machine_models": models,
        "usage": usage,
        "stock_snapshots": stock_snapshots,
        "tech_orders": tech_orders,
        "baseline_service_level": 0.25,
    }

    summary, weekly, _ = run_backtest(data, enforce_fail_conditions=False, output_dir=scenario_dir)

    result = summary.iloc[0]
    assert math.isclose(result["baseline_service_level"], 0.25, abs_tol=1e-4)
    assert math.isclose(result["model_service_level"], 0.9167, abs_tol=1e-4)
    assert math.isclose(result["service_level_improvement"], 0.6667, abs_tol=1e-4)

    partial = weekly[weekly["part_id"] == "P_PARTIAL"]
    assert int((partial["unfulfilled_qty"] > 0).sum()) == 1
