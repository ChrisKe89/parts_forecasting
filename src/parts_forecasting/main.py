from __future__ import annotations

import numpy as np
import pandas as pd

from parts_forecasting.backtest import run_rolling_backtest
from parts_forecasting.config import INPUT_FILES, OUTPUT_DATA_DIR, OUTPUT_FILE, SUMMARY_FILE
from parts_forecasting.feature_engineering import build_installed_base
from parts_forecasting.load_data import load_input_data
from parts_forecasting.prepare_data import clean_input_data, prepare_monthly_data


def summarize_results(results: pd.DataFrame) -> pd.DataFrame:
    if results.empty:
        return pd.DataFrame()
    errors = results["predicted_demand"] - results["true_demand"]
    return pd.DataFrame({
        "total_true_demand": [results["true_demand"].sum()],
        "total_predicted_demand": [results["predicted_demand"].sum()],
        "total_recommended_order": [results["recommended_order"].sum()],
        "MAE": [results["absolute_error"].mean()],
        "RMSE": [float(np.sqrt((errors**2).mean()))],
        "bias": [errors.mean()],
        "over_forecast_count": [(results["forecast_error"] > 0).sum()],
        "under_forecast_count": [(results["forecast_error"] < 0).sum()],
        "exact_zero_actual_count": [(results["true_demand"] == 0).sum()],
        "zero_actual_positive_forecast_count": [((results["true_demand"] == 0) & (results["predicted_demand"] > 0)).sum()],
    })


def run() -> None:
    OUTPUT_DATA_DIR.mkdir(parents=True, exist_ok=True)
    raw = load_input_data(INPUT_FILES)
    cleaned = clean_input_data(raw)
    monthly = prepare_monthly_data(cleaned)
    installed_base = build_installed_base(monthly["installs"])
    backtest_results = run_rolling_backtest(monthly, installed_base)
    backtest_results = backtest_results.replace([np.inf, -np.inf], 0).fillna(0)
    backtest_results.to_csv(OUTPUT_FILE, index=False)
    summarize_results(backtest_results).to_csv(SUMMARY_FILE, index=False)


if __name__ == "__main__":
    run()
