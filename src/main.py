from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd

from .data.loader import load_inputs
from .forecasting.engine import run_forecast
from .backtesting import run_backtest


def _can_run_backtest(usage: pd.DataFrame, min_months: int = 6) -> bool:
    if usage.empty:
        return False
    span_days = (usage["usage_date"].max() - usage["usage_date"].min()).days
    return span_days >= min_months * 30


def main() -> int:
    parser = argparse.ArgumentParser(description="Parts forecasting runtime")
    parser.add_argument("--input-dir", default="data/raw")
    parser.add_argument("--output-dir", default="data/output")
    parser.add_argument("--skip-backtest", action="store_true")
    parser.add_argument("--mode", choices=["forecast", "backtest", "all"], default="all")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    data, issues, valid = load_inputs(input_dir)
    issues.to_csv(output_dir / "schema_validation_report.csv", index=False)

    if not valid:
        errors = issues[issues["severity"] == "error"]["message"].tolist()
        for msg in errors:
            print(msg)
        print(f"Run failed: {len(errors)} validation error(s).")
        return 1

    validation_report = issues.copy()
    validation_report.to_csv(output_dir / "validation_report.csv", index=False)
    summary = pd.DataFrame([
        {"severity": "error", "issue_count": int((issues["severity"] == "error").sum()), "blocking_status": "blocking"},
        {"severity": "warning", "issue_count": int((issues["severity"] == "warning").sum()), "blocking_status": "non_blocking"},
    ])
    summary.to_csv(output_dir / "validation_summary.csv", index=False)

    forecast_df = None
    forecast_raw = None
    if args.mode in {"forecast", "all"}:
        forecast_raw = run_forecast(data)
        if "part_number" in forecast_raw.columns:
            forecast_raw = forecast_raw.groupby("part_number", as_index=False).first()
        elif "part_id" in forecast_raw.columns:
            forecast_raw = forecast_raw.groupby("part_id", as_index=False).first()
        forecast_df = forecast_raw.copy()
        forecast_df["part_number"] = forecast_df["part_number"] if "part_number" in forecast_df.columns else forecast_df["part_id"]
        forecast_df["base_forecast"] = forecast_df["forecast_demand"]
        forecast_df["final_adjusted_demand"] = forecast_df["forecast_demand"]
        forecast_df["stock_on_hand_qty"] = forecast_df["stock_on_hand"]
        forecast_df["allocated_qty"] = 0.0
        forecast_df["backorder_qty"] = 0.0
        forecast_df["effective_stock_qty"] = forecast_df["stock_on_hand_qty"] - forecast_df["allocated_qty"] - forecast_df["backorder_qty"]
        forecast_df["pipeline_supply_qty"] = forecast_df["stock_on_order"]
        forecast_df["projected_stock"] = forecast_df["effective_stock_qty"] + forecast_df["pipeline_supply_qty"] - forecast_df["lead_time_demand"]
        forecast_df["reorder_triggered"] = forecast_df["projected_stock"] < forecast_df["reorder_point"]
        forecast_df["required_quantity"] = (forecast_df["reorder_point"] - forecast_df["projected_stock"]).clip(lower=0)
        forecast_df["final_order_quantity"] = forecast_df["final_order_qty"]
        forecast_df["recommendation_explanation"] = forecast_df["explanation"]
        forecast_df = forecast_df[[
            "part_number", "base_forecast", "final_adjusted_demand", "stock_on_hand_qty", "allocated_qty", "backorder_qty",
            "effective_stock_qty", "pipeline_supply_qty", "lead_time_demand", "safety_stock", "reorder_point",
            "projected_stock", "reorder_triggered", "required_quantity", "final_order_quantity", "recommendation_explanation"
        ]]
        forecast_df.to_csv(output_dir / "forecast_output.csv", index=False)

    backtest_written = False
    backtest_reason = ""
    if (not args.skip_backtest) and args.mode in {"backtest", "all"}:
        if _can_run_backtest(data["usage"]):
            backtest_result = run_backtest(data)
            if isinstance(backtest_result, tuple):
                _summary_df, weekly_df, _concerns = backtest_result
                part_col = "part_id" if "part_id" in weekly_df.columns else "part_number"
                grp = weekly_df.groupby(part_col, as_index=False).agg(
                    period_start=("week_start_date", "min"),
                    period_end=("week_start_date", "max"),
                    actual_qty=("usage_qty", "sum"),
                )
                if forecast_raw is not None:
                    f_part_col = "part_number" if "part_number" in forecast_raw.columns else "part_id"
                    fc = forecast_raw[[f_part_col, "forecast_demand"]].rename(columns={f_part_col: part_col, "forecast_demand": "forecast_qty"})
                    grp = grp.merge(fc, on=part_col, how="left")
                else:
                    grp["forecast_qty"] = 0.0
                grp["error_qty"] = grp["forecast_qty"] - grp["actual_qty"]
                grp["abs_error"] = grp["error_qty"].abs()
                grp["squared_error"] = grp["error_qty"] ** 2
                grp = grp.rename(columns={part_col: "part_number"})
                backtest_df = grp[["part_number", "period_start", "period_end", "forecast_qty", "actual_qty", "error_qty", "abs_error", "squared_error"]]
                backtest_df = backtest_df.groupby("part_number", as_index=False).agg(
                    period_start=("period_start", "min"),
                    period_end=("period_end", "max"),
                    forecast_qty=("forecast_qty", "sum"),
                    actual_qty=("actual_qty", "sum"),
                    error_qty=("error_qty", "sum"),
                    abs_error=("abs_error", "sum"),
                    squared_error=("squared_error", "sum"),
                )
            else:
                backtest_df = backtest_result
            backtest_df.to_csv(output_dir / "backtest_output.csv", index=False)
            backtest_written = True
        else:
            backtest_reason = "Backtest skipped: insufficient usage history."

    install_available = not data["installs"].empty
    print(
        f"Run summary: forecast_rows={0 if forecast_df is None else len(forecast_df)}, "
        f"backtest_written={backtest_written}, warnings={int((issues['severity'] == 'warning').sum())}, "
        f"install_adjustment_available={install_available}"
    )
    if backtest_reason:
        print(backtest_reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
