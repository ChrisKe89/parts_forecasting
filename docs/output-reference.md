# Output Reference

## forecast_output.csv
- **Purpose:** Primary part-level forecast and reorder recommendation output.
- **Important columns:** part_number, base_forecast, final_adjusted_demand, stock_on_hand_qty, allocated_qty, backorder_qty, effective_stock_qty, pipeline_supply_qty, lead_time_demand, safety_stock, reorder_point, projected_stock, reorder_triggered, required_quantity, final_order_quantity, recommendation_explanation.
- **Decision grain:** exactly one recommendation row per active `part_number`; model-level signals are aggregated before inventory decisioning.
- **Interpretation:** Use to review demand outlook and whether reorder is triggered under current constraints.

## backtest_output.csv
- **Purpose:** Forecast-vs-actual detail for evaluation windows.
- **Important columns:** part_number, period_start, period_end, forecast_qty, actual_qty, error_qty, abs_error, squared_error.
- **Interpretation:** Granular performance diagnostics by part and test period.

## validation_report.csv
- **Purpose:** Runtime data and business-rule validation findings.
- **Important columns:** severity, check_name, file_name, row_number, message.
- **Interpretation:** Operational validation results; warnings allow continuation, errors typically block forecast.

## validation_summary.csv
- **Purpose:** Aggregated validation counts and status.
- **Important columns:** severity, issue_count, blocking_status.
- **Interpretation:** Quick health summary before consuming forecast outputs.

## schema_validation_report.csv
- **Purpose:** Schema-contract validation output for CSV structure/content checks.
- **Important columns:** file_name, column_name, row_number, severity, message.
- **Interpretation:** Canonical contract-compliance report; errors stop forecasting and warnings are retained for follow-up.


## Runtime behavior
- Default run: `python -m src.main`
- Default input directory: `data/raw`
- Default output directory: `data/output` (created automatically if missing)
- `install_forecast.csv` is optional; when missing, install adjustment is unavailable and treated as zero contribution.
- Backtest may be skipped when historical span is insufficient; forecast outputs are still written.
