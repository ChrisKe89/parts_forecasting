from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

from utils.config import DEFAULT_CONFIG


def generate_synthetic_data(output_dir: Path, seed: int = DEFAULT_CONFIG.random_seed) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    n_parts, n_models = 1000, 25
    parts = [f"P{i:04d}" for i in range(n_parts)]
    models = [f"M{i:02d}" for i in range(n_models)]
    behaviors = ["normal", "slow", "volatile", "up", "down", "sparse", "zero"]
    part_rows = []
    for p in parts:
        m = models[rng.integers(0, n_models)]
        part_rows.append({"part_number": p, "part_name": f"Part {p}", "model": m, "smoothing_group": rng.choice(["A", "B", "C"]), "minimum_order_quantity": int(rng.choice([0, 5, 10, 20, 50])), "lead_time_days": int(rng.integers(45, 121)), "behavior": rng.choice(behaviors)})
    parts_df = pd.DataFrame(part_rows)

    usage_dates = pd.date_range(end=pd.Timestamp("2026-04-30"), periods=24, freq="MS")
    usage_rows = []
    for _, p in parts_df.iterrows():
        for i, d in enumerate(usage_dates):
            base = {"normal": 30, "slow": 5, "volatile": 30, "up": 10 + i, "down": max(0, 35 - i), "sparse": 1 if i % 4 == 0 else 0, "zero": 0}[p.behavior]
            noise = rng.normal(0, 3 if p.behavior != "volatile" else 12)
            qty = max(0, int(round(base + noise)))
            if rng.random() < 0.005:
                qty *= 5
            usage_rows.append({"part_number": p.part_number, "model": p.model, "usage_date": d, "usage_qty": qty, "active_machines": int(rng.integers(20, 200))})
    usage_df = pd.DataFrame(usage_rows)

    install_rows = []
    hist_installs = pd.date_range(end=pd.Timestamp("2026-04-30"), periods=12, freq="MS")
    fut_sched = pd.date_range(start=pd.Timestamp("2026-05-01"), periods=6, freq="MS")
    fut_proj = pd.date_range(start=pd.Timestamp("2026-11-01"), periods=6, freq="MS")
    for _, p in parts_df.iterrows():
        for d in hist_installs:
            install_rows.append({"part_number": p.part_number, "model": p.model, "install_date": d, "install_qty": int(rng.integers(0, 10)), "install_status": "historical", "projected_install_confidence": 1.0})
        for d in fut_sched:
            install_rows.append({"part_number": p.part_number, "model": p.model, "install_date": d, "install_qty": int(rng.integers(0, 8)), "install_status": "scheduled", "projected_install_confidence": 1.0})
        for d in fut_proj:
            install_rows.append({"part_number": p.part_number, "model": p.model, "install_date": d, "install_qty": int(rng.integers(0, 8)), "install_status": "projected", "projected_install_confidence": float(rng.uniform(0.3, 0.95))})
    installs_df = pd.DataFrame(install_rows)

    stock_rows = []
    snaps = pd.date_range(end=pd.Timestamp("2026-04-30"), periods=52, freq="W")
    for _, p in parts_df.iterrows():
        risk = rng.choice(["stockout", "overstock", "normal"])
        for d in snaps:
            soh = int(rng.integers(0, 40) if risk == "stockout" else (rng.integers(200, 500) if risk == "overstock" else rng.integers(30, 150)))
            soo = int(rng.integers(0, 100))
            stock_rows.append({"part_number": p.part_number, "model": p.model, "snapshot_date": d, "stock_on_hand": soh, "stock_on_order": soo, "expected_arrival_date": d + pd.Timedelta(days=int(rng.integers(7, 140)))})
    stock_df = pd.DataFrame(stock_rows)

    parts_out = parts_df.drop(columns=["behavior"])
    for name, df in {"parts": parts_out, "usage": usage_df, "installs": installs_df, "stock": stock_df}.items():
        df.to_csv(output_dir / f"{name}.csv", index=False)
    return {"parts": parts_out, "usage": usage_df, "installs": installs_df, "stock": stock_df}
