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
        {"severity": "error", "count": int((issues["severity"] == "error").sum())},
        {"severity": "warning", "count": int((issues["severity"] == "warning").sum())},
    ])
    summary.to_csv(output_dir / "validation_summary.csv", index=False)

    forecast_df = None
    if args.mode in {"forecast", "all"}:
        forecast_df = run_forecast(data)
        forecast_df.to_csv(output_dir / "forecast_output.csv", index=False)

    backtest_written = False
    backtest_reason = ""
    if (not args.skip_backtest) and args.mode in {"backtest", "all"}:
        if _can_run_backtest(data["usage"]):
            backtest_df = run_backtest(data)
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
