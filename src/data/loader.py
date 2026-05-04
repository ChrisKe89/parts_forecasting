from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

REQUIRED_FILES = [
    "parts_master.csv",
    "part_model_mapping.csv",
    "internal_parts_usage.csv",
    "orders.csv",
    "stock_snapshot.csv",
    "open_purchase_orders.csv",
    "active_machine_population.csv",
]
OPTIONAL_FILES = ["install_forecast.csv"]

ALLOWED_ENUMS = {
    ("orders.csv", "order_source"): {"dealer", "direct", "internal", "other"},
    ("orders.csv", "order_status"): {"fulfilled", "partially_fulfilled", "backorder", "cancelled"},
    ("open_purchase_orders.csv", "purchase_order_status"): {"open", "partially_received", "received", "cancelled"},
    ("active_machine_population.csv", "owner_group"): {"direct", "customer", "dealer"},
    ("active_machine_population.csv", "service_group"): {"direct", "dealer"},
    ("install_forecast.csv", "install_status"): {"scheduled", "projected", "cancelled"},
}


def _issue(file_name: str, column_name: str, row_number: int, severity: str, message: str) -> dict[str, Any]:
    return {
        "file_name": file_name,
        "column_name": column_name,
        "row_number": row_number,
        "severity": severity,
        "message": message,
    }


def _validate_columns(df: pd.DataFrame, file_name: str, required_columns: list[str], issues: list[dict[str, Any]]) -> bool:
    ok = True
    for col in required_columns:
        if col not in df.columns:
            issues.append(_issue(file_name, col, 0, "error", f"Missing required column in {file_name}: {col}"))
            ok = False
    return ok


def _parse_date(df: pd.DataFrame, file_name: str, col: str, issues: list[dict[str, Any]]) -> None:
    parsed = pd.to_datetime(df[col], errors="coerce")
    bad = parsed.isna() & df[col].notna()
    for idx in df[bad].index.tolist():
        issues.append(_issue(file_name, col, int(idx) + 2, "error", f"Invalid date in {file_name} row {int(idx)+2}: {col}"))
    df[col] = parsed


def _non_negative(df: pd.DataFrame, file_name: str, col: str, issues: list[dict[str, Any]]) -> None:
    vals = pd.to_numeric(df[col], errors="coerce")
    bad_type = vals.isna() & df[col].notna()
    for idx in df[bad_type].index.tolist():
        issues.append(_issue(file_name, col, int(idx) + 2, "error", f"Invalid numeric value in {file_name} row {int(idx)+2}: {col}"))
    neg = vals < 0
    for idx in df[neg.fillna(False)].index.tolist():
        issues.append(_issue(file_name, col, int(idx) + 2, "error", f"Negative quantity in {file_name} row {int(idx)+2}: {col}"))
    df[col] = vals


def _validate_enum(df: pd.DataFrame, file_name: str, col: str, allowed: set[str], issues: list[dict[str, Any]]) -> None:
    normalized = df[col].astype(str).str.strip().str.lower()
    bad = ~normalized.isin(allowed)
    for idx in df[bad.fillna(False)].index.tolist():
        issues.append(_issue(file_name, col, int(idx) + 2, "error", f"Invalid enum in {file_name} row {int(idx)+2}: {col}={df.loc[idx, col]}"))


def _validate_confidence(df: pd.DataFrame, file_name: str, col: str, issues: list[dict[str, Any]]) -> None:
    vals = pd.to_numeric(df[col], errors="coerce")
    bad = vals.isna() | (vals < 0) | (vals > 1)
    for idx in df[bad.fillna(False)].index.tolist():
        issues.append(_issue(file_name, col, int(idx) + 2, "error", f"Confidence out of bounds [0,1] in {file_name} row {int(idx)+2}"))
    df[col] = vals


def load_inputs(base_dir: Path) -> tuple[dict[str, pd.DataFrame], pd.DataFrame, bool]:
    issues: list[dict[str, Any]] = []
    missing_required = [f for f in REQUIRED_FILES if not (base_dir / f).exists()]
    for f in missing_required:
        issues.append(_issue(f, "", 0, "error", f"Missing required input file: {base_dir / f}"))
    if missing_required:
        return {}, pd.DataFrame(issues, columns=["file_name", "column_name", "row_number", "severity", "message"]), False

    frames = {f: pd.read_csv(base_dir / f) for f in REQUIRED_FILES}
    install_available = (base_dir / "install_forecast.csv").exists()
    install_df = pd.read_csv(base_dir / "install_forecast.csv") if install_available else pd.DataFrame(columns=["model", "install_date", "install_qty", "install_status", "projected_install_confidence"])

    _validate_columns(frames["parts_master.csv"], "parts_master.csv", ["part_number", "part_description", "smoothing_group", "minimum_order_qty", "default_lead_time_days", "is_active"], issues)
    _validate_columns(frames["part_model_mapping.csv"], "part_model_mapping.csv", ["part_number", "model"], issues)
    _validate_columns(frames["internal_parts_usage.csv"], "internal_parts_usage.csv", ["part_number", "model", "usage_date", "usage_qty"], issues)
    _validate_columns(frames["orders.csv"], "orders.csv", ["order_no", "part_number", "order_qty", "fulfilled_qty", "order_date", "order_source", "order_status", "order_fulfilment_date"], issues)
    _validate_columns(frames["stock_snapshot.csv"], "stock_snapshot.csv", ["part_number", "stock_snapshot_date", "stock_on_hand_qty", "allocated_qty"], issues)
    _validate_columns(frames["open_purchase_orders.csv"], "open_purchase_orders.csv", ["purchase_order_no", "part_number", "purchase_order_qty", "received_qty", "open_purchase_order_qty", "purchase_order_date", "purchase_order_status", "expected_arrival_date"], issues)
    _validate_columns(frames["active_machine_population.csv"], "active_machine_population.csv", ["model", "population_snapshot_date", "active_machine_qty", "owner_group", "service_group"], issues)
    _validate_columns(install_df, "install_forecast.csv", ["model", "install_date", "install_qty", "install_status", "projected_install_confidence"], issues)

    for (f, c), allowed in ALLOWED_ENUMS.items():
        df = install_df if f == "install_forecast.csv" else frames[f]
        if c in df.columns:
            _validate_enum(df, f, c, allowed, issues)

    usage = frames["internal_parts_usage.csv"].copy()
    _parse_date(usage, "internal_parts_usage.csv", "usage_date", issues)
    _non_negative(usage, "internal_parts_usage.csv", "usage_qty", issues)

    parts = frames["parts_master.csv"].copy().rename(columns={"part_description": "part_name", "minimum_order_qty": "minimum_order_quantity", "default_lead_time_days": "lead_time_days"})
    _non_negative(parts, "parts_master.csv", "minimum_order_quantity", issues)
    _non_negative(parts, "parts_master.csv", "lead_time_days", issues)
    mapping = frames["part_model_mapping.csv"].copy()
    parts = parts.merge(mapping, on="part_number", how="inner")

    pop = frames["active_machine_population.csv"].copy()
    _parse_date(pop, "active_machine_population.csv", "population_snapshot_date", issues)
    _non_negative(pop, "active_machine_population.csv", "active_machine_qty", issues)
    usage = usage.merge(pop[["model", "active_machine_qty"]], on="model", how="left")
    missing_pop = usage["active_machine_qty"].isna()
    for idx in usage[missing_pop].index.tolist():
        issues.append(_issue("active_machine_population.csv", "model", int(idx)+2, "warning", f"Unknown model in usage population join: {usage.loc[idx, 'model']}"))
    usage["active_machines"] = usage["active_machine_qty"].fillna(0)

    stock = frames["stock_snapshot.csv"].copy()
    _parse_date(stock, "stock_snapshot.csv", "stock_snapshot_date", issues)
    _non_negative(stock, "stock_snapshot.csv", "stock_on_hand_qty", issues)
    _non_negative(stock, "stock_snapshot.csv", "allocated_qty", issues)

    orders = frames["orders.csv"].copy()
    _parse_date(orders, "orders.csv", "order_date", issues)
    _parse_date(orders, "orders.csv", "order_fulfilment_date", issues)
    _non_negative(orders, "orders.csv", "order_qty", issues)
    _non_negative(orders, "orders.csv", "fulfilled_qty", issues)
    bad_fulfilled = orders["fulfilled_qty"] > orders["order_qty"]
    for idx in orders[bad_fulfilled.fillna(False)].index.tolist():
        issues.append(_issue("orders.csv", "fulfilled_qty", int(idx)+2, "error", "fulfilled_qty cannot exceed order_qty"))

    backorder = orders.copy()
    backorder["unfulfilled_qty"] = (backorder["order_qty"] - backorder["fulfilled_qty"]).clip(lower=0)
    backorder = backorder[backorder["order_status"].isin(["partially_fulfilled", "backorder"])].groupby("part_number", as_index=False)["unfulfilled_qty"].sum()

    po = frames["open_purchase_orders.csv"].copy()
    _parse_date(po, "open_purchase_orders.csv", "purchase_order_date", issues)
    _parse_date(po, "open_purchase_orders.csv", "expected_arrival_date", issues)
    _non_negative(po, "open_purchase_orders.csv", "purchase_order_qty", issues)
    _non_negative(po, "open_purchase_orders.csv", "received_qty", issues)
    _non_negative(po, "open_purchase_orders.csv", "open_purchase_order_qty", issues)
    po_delta = (po["purchase_order_qty"] - po["received_qty"]).round(6)
    bad_po = (po_delta - po["open_purchase_order_qty"]).abs() > 1e-6
    for idx in po[bad_po.fillna(False)].index.tolist():
        issues.append(_issue("open_purchase_orders.csv", "open_purchase_order_qty", int(idx)+2, "error", "open_purchase_order_qty must equal purchase_order_qty - received_qty"))

    stock = stock.merge(backorder, on="part_number", how="left").fillna({"unfulfilled_qty": 0})
    stock = stock.merge(po[["part_number", "expected_arrival_date", "open_purchase_order_qty"]], on="part_number", how="left")
    stock = stock.rename(columns={"stock_snapshot_date": "snapshot_date"})
    stock["open_purchase_order_qty"] = stock["open_purchase_order_qty"].fillna(0)
    stock["expected_arrival_date"] = pd.to_datetime(stock["expected_arrival_date"], errors="coerce").fillna(stock["snapshot_date"])

    installs = install_df.copy()
    if install_available:
        _parse_date(installs, "install_forecast.csv", "install_date", issues)
        _non_negative(installs, "install_forecast.csv", "install_qty", issues)
        _validate_confidence(installs, "install_forecast.csv", "projected_install_confidence", issues)

    has_errors = any(i["severity"] == "error" for i in issues)
    data = {
        "parts": parts[["part_number", "part_name", "model", "smoothing_group", "minimum_order_quantity", "lead_time_days"]],
        "usage": usage[["part_number", "model", "usage_date", "usage_qty", "active_machines"]],
        "installs": installs[["part_number", "model", "install_date", "install_qty", "install_status", "projected_install_confidence"]] if "part_number" in installs.columns else pd.DataFrame(columns=["part_number", "model", "install_date", "install_qty", "install_status", "projected_install_confidence"]),
        "stock": stock[["part_number", "snapshot_date", "stock_on_hand_qty", "allocated_qty", "unfulfilled_qty", "open_purchase_order_qty", "expected_arrival_date"]],
    }
    return data, pd.DataFrame(issues, columns=["file_name", "column_name", "row_number", "severity", "message"]), (not has_errors)
