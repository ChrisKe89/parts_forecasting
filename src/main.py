from __future__ import annotations

import argparse
from pathlib import Path

from .backtesting import run_backtest
from .data.loader import load_inputs
from .forecasting.engine import run_forecast


def main() -> int:
    parser = argparse.ArgumentParser(description="Parts forecasting runtime")
    parser.add_argument("--input-dir", default="data/raw")
    parser.add_argument("--output-dir", default="data/output")
    parser.add_argument("--mode", choices=["forecast", "backtest"], default="forecast")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    data, issues, valid = load_inputs(Path(args.input_dir))
    issues.to_csv(output_dir / "schema_validation_report.csv", index=False)
    if not valid:
        return 1

    if args.mode == "forecast":
        forecast = run_forecast(data)
        forecast.to_csv(output_dir / "forecast_recommendations.csv", index=False)
        print(f"Run summary: forecast_recommendations={len(forecast)}")
        return 0

    summary, weekly, concerns = run_backtest(data, enforce_fail_conditions=False, output_dir=output_dir)
    weekly.to_csv(output_dir / "inventory_position_simulation.csv", index=False)
    forecast = run_forecast(data)
    forecast.to_csv(output_dir / "model_recommendations.csv", index=False)
    print(f"Run summary: backtest_rows={len(weekly)}, concerns={len(concerns['concerns'])}, summary_rows={len(summary)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
