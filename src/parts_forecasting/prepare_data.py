"""Data cleaning and aggregation helpers."""

from __future__ import annotations

from typing import Dict

import pandas as pd


def _standardize_common_fields(df: pd.DataFrame, has_model: bool = True) -> pd.DataFrame:
    if df.empty:
        return df

    normalized = df.copy()
    normalized.columns = [col.strip().lower() for col in normalized.columns]

    if "part_number" in normalized.columns:
        normalized["part_number"] = normalized["part_number"].astype(str).str.upper().str.strip()
    if has_model and "model" in normalized.columns:
        normalized["model"] = normalized["model"].astype(str).str.upper().str.strip()

    if "date" in normalized.columns:
        normalized["date"] = pd.to_datetime(normalized["date"], errors="coerce")

    if "qty" in normalized.columns:
        normalized["qty"] = pd.to_numeric(normalized["qty"], errors="coerce")

    key_columns = [c for c in ["part_number", "model", "date", "qty"] if c in normalized.columns]
    normalized = normalized.dropna(subset=key_columns)
    return normalized


def clean_input_data(data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    cleaned = {}
    cleaned["usage"] = _standardize_common_fields(data["usage"], has_model=True)
    cleaned["installs"] = _standardize_common_fields(data["installs"], has_model=True)
    cleaned["emergency"] = _standardize_common_fields(data["emergency"], has_model=False)
    cleaned["cannibalised"] = _standardize_common_fields(data["cannibalised"], has_model=False)

    mapping = data["mapping"].copy()
    if not mapping.empty:
        mapping.columns = [col.strip().lower() for col in mapping.columns]
        mapping["part_number"] = mapping["part_number"].astype(str).str.upper().str.strip()
        mapping["model"] = mapping["model"].astype(str).str.upper().str.strip()
        mapping = mapping.dropna(subset=["part_number", "model"])
    cleaned["mapping"] = mapping

    stock = data["stock"].copy()
    if not stock.empty:
        stock.columns = [col.strip().lower() for col in stock.columns]
        stock["part_number"] = stock["part_number"].astype(str).str.upper().str.strip()
        stock["stock_on_hand"] = pd.to_numeric(stock["stock_on_hand"], errors="coerce").fillna(0)
        stock["stock_on_order"] = pd.to_numeric(stock["stock_on_order"], errors="coerce").fillna(0)
        stock["snapshot_date"] = pd.to_datetime(stock["snapshot_date"], errors="coerce")
        stock = stock.dropna(subset=["part_number", "snapshot_date"])
    cleaned["stock"] = stock

    return cleaned


def aggregate_monthly(df: pd.DataFrame, group_columns: list[str]) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=group_columns + ["month", "qty"])
    monthly = df.copy()
    monthly["month"] = monthly["date"].dt.to_period("M").dt.to_timestamp()
    return monthly.groupby(group_columns + ["month"], as_index=False)["qty"].sum()


def prepare_monthly_data(cleaned: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    usage = aggregate_monthly(cleaned["usage"], ["part_number", "model"])
    installs = aggregate_monthly(cleaned["installs"], ["model"])

    emergency_input = cleaned["emergency"]
    if emergency_input.empty:
        emergency = pd.DataFrame(columns=["part_number", "model", "month", "qty"])
    else:
        emergency = emergency_input.merge(cleaned["mapping"], on="part_number", how="left")
        emergency = emergency.dropna(subset=["model"])
        emergency = aggregate_monthly(emergency, ["part_number", "model"])

    cannibalised_input = cleaned["cannibalised"]
    if cannibalised_input.empty:
        cannibalised = pd.DataFrame(columns=["part_number", "model", "month", "qty"])
    else:
        cannibalised = cannibalised_input.merge(cleaned["mapping"], on="part_number", how="left")
        cannibalised = cannibalised.dropna(subset=["model"])
        cannibalised = aggregate_monthly(cannibalised, ["part_number", "model"])

    return {
        "usage": usage,
        "installs": installs,
        "emergency": emergency,
        "cannibalised": cannibalised,
        "stock": cleaned["stock"],
        "mapping": cleaned["mapping"],
    }
