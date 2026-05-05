# Output Reference

## Forecast mode (`python -m src.main --mode forecast`)

### forecast_recommendations.csv

- **Purpose:** Live recommendation output (no historical replay).
- **Important columns:** `part_number` or `part_id`, `base_forecast_demand`, `dealer_demand`, `install_adjustment`, `forecast_demand`, `forecast_method`, `forecast_trend`, `outlier_count`, `max_abs_z_score`, `usage_per_machine`, `lead_time_demand`, `safety_stock`, `reorder_point`, `stock_on_hand`, `stock_on_order`, `allocated_qty`, `backorder_qty`, `effective_stock`, `pipeline_supply`, `projected_stock`, `raw_recommended_qty`, `final_order_qty`, `minimum_order_qty`, `order_multiple_qty`, `moq_applied`, `order_multiple_applied`, `risk_level`, `explanation`, `demand_source`.
- **Demand contract:** `forecast_demand` combines documented demand signals only: internal usage base forecast, dealer-order contribution, and install adjustment. `demand_source` identifies which of those signals contributed to the part-level recommendation.
- **Forecast method contract:** `forecast_method` is `exponential_smoothing` unless the configured Holt minimum-history and trend-significance gates pass.
- **Inventory contract:** `effective_stock = stock_on_hand - allocated_qty - backorder_qty`; `pipeline_supply` includes open purchase order quantities expected on or before the part lead-time target date.

## Backtest/proof mode (`python -m src.main --mode backtest`)

### backtest_summary.json

- **Purpose:** Top-line proof answer for baseline vs model outcomes.
- **Includes:**
  - `baseline_service_level`, `model_service_level`, `service_level_improvement`
  - `baseline_fill_rate`, `model_fill_rate`, `fill_rate_improvement`
  - `baseline_stockout_count`, `model_stockout_count`, `stockout_reduction`
  - `average_inventory_baseline`, `average_inventory_model`, `inventory_change`, `inventory_change_percent`
  - `peak_inventory_baseline`, `peak_inventory_model`
  - `total_ordered_qty_baseline`, `total_ordered_qty_model`, `total_received_qty_model`
  - `total_open_order_qty_end`, `total_backorder_qty_end`
  - `true_demand`, `model_fulfilled_qty`, `model_unfulfilled_qty`
  - supplier lifecycle summary fields (`total_supplier_orders_created`, `total_partial_receipts`, `total_delayed_receipts`, `total_cancelled_qty`, `total_remaining_open_qty`, status counts)

### backtest_weekly_detail.csv

- **Purpose:** Weekly replay detail at part-week grain.
- **Important columns:** `opening_stock`, `usage_qty`, `fulfilled_qty`, `unfulfilled_qty`, `receipts_qty`, `backorder_qty`, `stock_on_order`, `closing_stock`, `raw_recommended_qty`, `final_order_qty`, MOQ/multiple flags.

### concerns_report.json

- **Purpose:** Structured PRD concern checks + human-readable result summary.
- **Shape:**

  ```json
  {
    "concerns": [{"type": "service_level", "severity": "high", "message": "..."}],
    "human_readable_summary": {
      "result": "improved|not_improved",
      "baseline_service_level": 0.60,
      "model_service_level": 0.78,
      "service_level_improvement": 0.18
    }
  }
  ```

### supplier_order_simulation.csv

- **Purpose:** Supplier lifecycle records during replay.
- **Important columns:** `supplier_order_id`, `part_id`, `order_date`, `original_order_qty`, `received_qty`, `cancelled_qty`, `remaining_qty`, `expected_arrival_date`, `actual_arrival_date`, `receipt_status`.
- **Status values:** `open`, `partial`, `full`, `delayed`, `cancelled`.

### inventory_position_simulation.csv

- **Purpose:** Persisted copy of weekly stock position simulation for audit tooling.

### model_recommendations.csv

- **Purpose:** Current model recommendations written during backtest run for side-by-side inspection.

## Validation output

### schema_validation_report.csv

- **Purpose:** Canonical schema-contract validation output.
- **Behavior:** Errors block execution; warnings continue and are reported.
