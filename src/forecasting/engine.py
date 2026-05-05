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
from ..inventory.logic import apply_order_constraints, demand_during_lead_time, reorder_point
from ..utils.config import DEFAULT_CONFIG, ForecastingConfig


def _first_existing(columns: pd.Index, candidates: list[str]) -> str | None:
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


def _known_date(data: dict[str, pd.DataFrame], usage_date_col: str | None, stock_date_col: str | None) -> pd.Timestamp:
    dates: list[pd.Timestamp] = []
    usage = data.get("usage", pd.DataFrame())
    stock = data.get("stock", data.get("stock_snapshots", pd.DataFrame()))
    if usage_date_col and not usage.empty:
        usage_dates = pd.to_datetime(usage[usage_date_col], errors="coerce").dropna()
        if not usage_dates.empty:
            dates.append(usage_dates.max())
    if stock_date_col and not stock.empty:
        stock_dates = pd.to_datetime(stock[stock_date_col], errors="coerce").dropna()
        if not stock_dates.empty:
            dates.append(stock_dates.max())
    return max(dates) if dates else pd.Timestamp("1970-01-01")


def _period_demand(hist: pd.DataFrame, usage_date_col: str | None) -> list[float]:
    if hist.empty:
        return [0.0]
    if usage_date_col:
        demand = hist.groupby(usage_date_col, as_index=True)["usage_qty"].sum().sort_index()
        return demand.astype(float).tolist() or [0.0]
    return hist["usage_qty"].astype(float).tolist() or [0.0]


def _dealer_demand_per_period(
    orders: pd.DataFrame,
    part_col: str,
    part_value: str,
    observed_periods: int,
) -> float:
    if orders.empty or part_col not in orders.columns or "order_source" not in orders.columns or "order_qty" not in orders.columns:
        return 0.0
    part_orders = orders[orders[part_col] == part_value].copy()
    if part_orders.empty:
        return 0.0
    dealer = part_orders[part_orders["order_source"].astype(str).str.lower() == "dealer"]
    if "order_status" in dealer.columns:
        dealer = dealer[dealer["order_status"].astype(str).str.lower() != "cancelled"]
    if dealer.empty:
        return 0.0
    period_count = max(observed_periods, 1)
    return float(pd.to_numeric(dealer["order_qty"], errors="coerce").fillna(0).sum() / period_count)


def _stock_position(
    stock: pd.DataFrame,
    part_col: str,
    part_value: str,
    target_date: pd.Timestamp,
) -> dict[str, float]:
    if stock.empty or part_col not in stock.columns:
        return {
            "stock_on_hand": 0.0,
            "allocated_qty": 0.0,
            "backorder_qty": 0.0,
            "effective_stock": 0.0,
            "pipeline_supply": 0.0,
        }

    st = stock[stock[part_col] == part_value].copy()
    if st.empty:
        return {
            "stock_on_hand": 0.0,
            "allocated_qty": 0.0,
            "backorder_qty": 0.0,
            "effective_stock": 0.0,
            "pipeline_supply": 0.0,
        }

    snapshot_col = _first_existing(st.columns, ["snapshot_date", "stock_snapshot_date"])
    if snapshot_col:
        st[snapshot_col] = pd.to_datetime(st[snapshot_col], errors="coerce")
        latest_snapshot = st[snapshot_col].max()
        snapshot_rows = st[st[snapshot_col] == latest_snapshot]
    else:
        snapshot_rows = st.tail(1)

    latest = snapshot_rows.iloc[-1]
    stock_on_hand_col = _first_existing(st.columns, ["stock_on_hand_qty", "stock_on_hand"])
    allocated_col = "allocated_qty" if "allocated_qty" in st.columns else None
    backorder_col = _first_existing(st.columns, ["unfulfilled_qty", "backorder_qty"])
    pipeline_col = _first_existing(st.columns, ["open_purchase_order_qty", "stock_on_order"])
    arrival_col = _first_existing(st.columns, ["expected_arrival_date", "arrival_date"])

    stock_on_hand = float(latest.get(stock_on_hand_col, 0.0) if stock_on_hand_col else 0.0)
    allocated_qty = float(latest.get(allocated_col, 0.0) if allocated_col else 0.0)
    backorder_qty = float(latest.get(backorder_col, 0.0) if backorder_col else 0.0)

    pipeline_supply = 0.0
    if pipeline_col:
        if arrival_col:
            arrivals = pd.to_datetime(st[arrival_col], errors="coerce")
            pipeline_rows = st[arrivals <= target_date]
        else:
            pipeline_rows = st
        pipeline_supply = float(pd.to_numeric(pipeline_rows[pipeline_col], errors="coerce").fillna(0).sum())

    effective_stock = stock_on_hand - allocated_qty - backorder_qty
    return {
        "stock_on_hand": stock_on_hand,
        "allocated_qty": allocated_qty,
        "backorder_qty": backorder_qty,
        "effective_stock": float(effective_stock),
        "pipeline_supply": pipeline_supply,
    }


def _install_adjustment(
    installs: pd.DataFrame,
    part_col: str,
    model_col: str | None,
    part_value: str,
    part_models: set[str],
    usage_rate_by_model: dict[str, float],
    as_of_date: pd.Timestamp,
    target_date: pd.Timestamp,
) -> float:
    if installs.empty or "install_qty" not in installs.columns or "install_status" not in installs.columns:
        return 0.0
    candidates = installs.copy()
    if part_col in candidates.columns:
        candidates = candidates[candidates[part_col] == part_value]
    if model_col and model_col in candidates.columns and part_models:
        candidates = candidates[candidates[model_col].isin(part_models)]
    if "install_date" in candidates.columns:
        install_dates = pd.to_datetime(candidates["install_date"], errors="coerce")
        candidates = candidates[(install_dates > as_of_date) & (install_dates <= target_date)]
    if candidates.empty:
        return 0.0

    adjustment = 0.0
    for row in candidates.itertuples(index=False):
        status = str(getattr(row, "install_status")).lower()
        if status == "cancelled":
            continue
        confidence = 1.0 if status == "scheduled" else float(getattr(row, "projected_install_confidence", 0.0) or 0.0)
        model = str(getattr(row, model_col)) if model_col and hasattr(row, model_col) else ""
        usage_rate = usage_rate_by_model.get(model, 0.0)
        adjustment += float(getattr(row, "install_qty", 0.0) or 0.0) * confidence * usage_rate
    return float(adjustment)


def _base_forecast(values: list[float], smoothing_group: str, config: ForecastingConfig) -> tuple[float, str, float]:
    alpha = float(config.smoothing_groups.get(smoothing_group, config.smoothing_groups.get("B", 0.4)))
    smoothed = exponential_smoothing(values, alpha)
    if len(values) < config.minimum_history_points_for_holt:
        return smoothed, "exponential_smoothing", 0.0
    holt_value, trend = holt_forecast(values, alpha, config.beta)
    trend_ratio = abs(trend) / max(abs(smoothed), 1.0)
    if trend_ratio >= config.trend_significance_threshold:
        return max(0.0, holt_value), "holt", trend
    return smoothed, "exponential_smoothing", trend


def run_forecast(
    data: dict[str, pd.DataFrame],
    as_of_date: pd.Timestamp | None = None,
    config: ForecastingConfig = DEFAULT_CONFIG,
) -> pd.DataFrame:
    parts = data["parts"]
    usage = data["usage"]
    stock = data.get("stock", data.get("stock_snapshots", pd.DataFrame()))
    orders = data.get("orders", pd.DataFrame())
    installs = data.get("installs", pd.DataFrame())
    part_col = "part_number" if "part_number" in parts.columns else "part_id"
    usage_part_col = part_col if part_col in usage.columns else _first_existing(usage.columns, ["part_number", "part_id"])
    model_col = _first_existing(parts.columns, ["model", "model_id"])
    usage_model_col = _first_existing(usage.columns, ["model", "model_id"])
    usage_date_col = _first_existing(usage.columns, ["usage_date", "week_start_date"])
    stock_part_col = part_col if part_col in stock.columns else _first_existing(stock.columns, ["part_number", "part_id"])
    min_order_col = "minimum_order_quantity" if "minimum_order_quantity" in parts.columns else "minimum_order_qty"
    order_multiple_col = "order_multiple_qty" if "order_multiple_qty" in parts.columns else None
    stock_date_col = _first_existing(stock.columns, ["snapshot_date", "stock_snapshot_date"])
    as_of = pd.Timestamp(as_of_date) if as_of_date is not None else _known_date(data, usage_date_col, stock_date_col)
    service_z = service_level_to_z(config.service_level_target)
    rows = []
    for part_value, part_rows in parts.groupby(part_col, sort=True):
        p = part_rows.iloc[0]
        hist = usage[usage[usage_part_col] == part_value].copy() if usage_part_col else pd.DataFrame()
        if usage_date_col and not hist.empty:
            hist = hist.sort_values(usage_date_col)
        vals = _period_demand(hist, usage_date_col)
        outliers = zscore_outliers(pd.Series(vals, dtype=float), config.z_threshold)
        smoothing_group = str(p.get("smoothing_group", "B"))
        base_demand, forecast_method, forecast_trend = _base_forecast(vals, smoothing_group, config)

        dealer_demand = _dealer_demand_per_period(orders, part_col, str(part_value), len(vals))
        part_models = set(part_rows[model_col].astype(str)) if model_col else set()
        usage_model = usage_model_col or model_col
        usage_rates = pd.DataFrame()
        if usage_model and usage_model in hist.columns and usage_part_col and usage_part_col in hist.columns and "active_machines" in hist.columns and not hist.empty:
            usage_rates = usage_per_machine(hist.rename(columns={usage_part_col: "part_number", usage_model: "model"}))
        usage_rate_by_model = {
            str(row.model): float(row.usage_per_machine)
            for row in usage_rates.itertuples(index=False)
        } if not usage_rates.empty else {}
        aggregate_usage_per_machine = float(sum(usage_rate_by_model.values()))

        lead_time_days = float(p.get("lead_time_days", config.lead_time_days_default))
        target_date = as_of + pd.Timedelta(days=lead_time_days)
        install_adjustment = _install_adjustment(
            installs,
            part_col,
            model_col,
            str(part_value),
            part_models,
            usage_rate_by_model,
            as_of,
            target_date,
        )
        weekly = float(base_demand + dealer_demand + install_adjustment)
        lead_time_d = demand_during_lead_time(weekly, lead_time_days, period_days=7)
        demand_std_dev = float(pd.Series(vals, dtype=float).std(ddof=0))
        lead_time_periods = max(lead_time_days, 0.0) / 7
        ss = safety_stock(demand_std_dev, lead_time_periods, service_z)
        rop = reorder_point(lead_time_d, ss)
        position = _stock_position(stock, stock_part_col or part_col, part_value, target_date)
        projected_stock = position["effective_stock"] + position["pipeline_supply"] - lead_time_d
        reorder_triggered = projected_stock < rop
        raw = max(0.0, rop - projected_stock) if reorder_triggered else 0.0
        order_multiple = float(p.get(order_multiple_col, 1.0)) if order_multiple_col else 1.0
        c = apply_order_constraints(raw, float(p.get(min_order_col, config.moq_default)), order_multiple)
        demand_sources = ["usage"]
        if dealer_demand > 0:
            demand_sources.append("dealer")
        if install_adjustment > 0:
            demand_sources.append("install")
        rows.append({
            part_col: part_value,
            "base_forecast_demand": base_demand,
            "dealer_demand": dealer_demand,
            "install_adjustment": install_adjustment,
            "forecast_demand": weekly,
            "forecast_method": forecast_method,
            "forecast_trend": float(forecast_trend),
            "outlier_count": int(outliers["outlier_flag"].sum()),
            "max_abs_z_score": float(outliers["z_score"].abs().max()),
            "usage_per_machine": aggregate_usage_per_machine,
            "lead_time_demand": lead_time_d,
            "safety_stock": ss,
            "reorder_point": rop,
            "stock_on_hand": position["stock_on_hand"],
            "stock_on_order": position["pipeline_supply"],
            "allocated_qty": position["allocated_qty"],
            "backorder_qty": position["backorder_qty"],
            "effective_stock": position["effective_stock"],
            "pipeline_supply": position["pipeline_supply"],
            "projected_stock": projected_stock,
            "minimum_order_qty": float(p.get(min_order_col, config.moq_default)),
            "order_multiple_qty": order_multiple,
            "demand_source": "_".join(demand_sources) if len(demand_sources) > 1 else "usage_only",
            "risk_level": "high" if raw > 0 else "low",
            "explanation": (
                f"{forecast_method} base demand plus documented demand adjustments; "
                "reorder based on projected stock versus ROP"
            ),
            **c,
        })
    return pd.DataFrame(rows)
