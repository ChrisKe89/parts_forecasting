from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd


def generate_synthetic_data(output_dir: Path, seed: int = 42) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    n_parts, n_models = 1000, 50
    parts = pd.DataFrame({
        "part_id": [f"P{i:05d}" for i in range(n_parts)],
        "part_description": [f"Part {i}" for i in range(n_parts)],
        "minimum_order_qty": rng.choice([5, 10, 20], n_parts),
        "order_multiple_qty": rng.choice([1, 5, 10], n_parts),
        "preferred_supplier_id": [f"S{rng.integers(1,40):03d}" for _ in range(n_parts)],
        "lead_time_days": rng.integers(14, 63, n_parts),
        "unit_cost": rng.uniform(5, 250, n_parts).round(2),
    })
    models = pd.DataFrame({"model_id": [f"M{i:03d}" for i in range(n_models)]})
    weeks = pd.date_range("2024-05-06", periods=104, freq="W-MON")
    usage_rows = []
    for p in parts["part_id"]:
        mid = models.sample(1, random_state=int(rng.integers(0, 1_000_000))).iloc[0]["model_id"]
        pattern = rng.choice(["intermittent", "high", "lumpy", "seasonal", "slow", "obsolete"])
        for i, w in enumerate(weeks):
            if pattern == "high": qty = max(0, int(rng.normal(30, 12)))
            elif pattern == "lumpy": qty = int(rng.choice([0, 0, 5, 40, 70]))
            elif pattern == "seasonal": qty = max(0, int(10 + 8 * np.sin(i / 6) + rng.normal(0, 3)))
            elif pattern == "slow": qty = int(rng.choice([0, 1, 2]))
            elif pattern == "obsolete": qty = 0 if i > 20 else int(rng.choice([0, 1]))
            else: qty = int(rng.choice([0, 0, 1, 3, 6]))
            usage_rows.append({"part_id": p, "model_id": mid, "week_start_date": w, "usage_qty": qty})
    usage = pd.DataFrame(usage_rows)
    stock = pd.DataFrame({"part_id": parts["part_id"], "snapshot_date": pd.Timestamp("2026-04-27"), "stock_on_hand": rng.integers(0, 20, n_parts), "stock_on_order": rng.integers(0, 15, n_parts), "allocated_qty": rng.integers(0, 5, n_parts)})
    tech_orders = usage[["part_id", "model_id", "week_start_date"]].rename(columns={"week_start_date": "order_date"}).copy()
    tech_orders["tech_order_qty"] = (usage["usage_qty"] * rng.uniform(0.7, 1.1, len(usage))).round().astype(int)
    tech_orders["fulfilled_qty"] = (tech_orders["tech_order_qty"] * rng.uniform(0.45, 0.65, len(usage))).round().clip(lower=0).astype(int)
    tech_orders["unfulfilled_qty"] = (tech_orders["tech_order_qty"] - tech_orders["fulfilled_qty"]).clip(lower=0)
    supplier_orders = pd.DataFrame(columns=["supplier_order_id","part_id","order_date","original_order_qty","received_qty","remaining_qty","expected_arrival_date","actual_arrival_date","receipt_status"])
    open_po = pd.DataFrame(columns=["supplier_order_id","part_id","order_date","original_order_qty","remaining_qty","expected_arrival_date"])
    data = {"parts": parts, "machine_models": models, "usage": usage, "tech_orders": tech_orders, "supplier_orders": supplier_orders, "stock_snapshots": stock, "backorders": tech_orders[["part_id","order_date","unfulfilled_qty"]], "open_purchase_orders": open_po, "data_source": "synthetic", "baseline_service_level": 0.60}
    for k, v in data.items():
        if isinstance(v, pd.DataFrame):
            v.to_csv(output_dir / f"{k}.csv", index=False)
    return data
