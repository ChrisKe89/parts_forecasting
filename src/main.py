"""Entry point for V1 lead-time-aware forecasting prototype."""

from __future__ import annotations

import pandas as pd

from src.backtest import run_rolling_backtest
from src.config import INPUT_FILES, OUTPUT_DATA_DIR, OUTPUT_FILE
from src.feature_engineering import build_installed_base
from src.load_data import load_input_data
from src.prepare_data import clean_input_data, prepare_monthly_data


def summarize_results(results: pd.DataFrame) -> pd.DataFrame:
    if results.empty:
        return pd.DataFrame()

    summary = pd.DataFrame(
        {
            "mae": [results["absolute_error"].mean()],
            "total_under_forecast": [results["under_forecast_qty"].sum()],
            "total_over_forecast": [results["over_forecast_qty"].sum()],
            "mean_predicted_demand": [results["predicted_demand"].mean()],
            "mean_true_demand": [results["true_demand"].mean()],
        }
    )
    return summary


def run() -> None:
    OUTPUT_DATA_DIR.mkdir(parents=True, exist_ok=True)

    raw_data = load_input_data(INPUT_FILES)
    cleaned_data = clean_input_data(raw_data)
    monthly_data = prepare_monthly_data(cleaned_data)
    installed_base_df = build_installed_base(monthly_data["installs"])

    backtest_results = run_rolling_backtest(monthly_data, installed_base_df)
    backtest_results.to_csv(OUTPUT_FILE, index=False)

    summary = summarize_results(backtest_results)
    summary_file = OUTPUT_DATA_DIR / "forecast_backtest_summary.csv"
    summary.to_csv(summary_file, index=False)


if __name__ == "__main__":
    run()
