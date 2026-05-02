# Output Reference

## forecast_output.csv
- **Purpose:** Primary part-level forecast and reorder recommendation output.
- **Important columns:** part_number, base_forecast, final_demand, effective_stock, pipeline_supply, lead_time_demand, safety_stock, reorder_point, projected_stock, recommended_order_qty, minimum_order_qty.
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
