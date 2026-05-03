# System Architecture

## System Flow
1. Load required and optional CSV files.
2. Validate schema and cross-table integrity.
3. Build demand history from internal usage + dealer demand.
4. Apply outlier handling and compute usage-per-machine signals.
5. Generate part-level base forecast.
6. Apply install demand adjustments (model-supported, part-level output).
7. Compute inventory position and reorder recommendations.
8. Write forecast, backtest, and validation outputs.

## Module Responsibilities
- `src/data`: data loading and schema validation.
- `src/forecasting`: demand preparation and forecasting calculations.
- `src/inventory`: stock position, reorder point, MOQ application.
- `src/backtesting`: train/test windows and performance metrics.
- `src/utils`: configuration and shared helpers.

## Demand/Supply Separation
- **Demand history:** internal usage and dealer demand.
- **Current stock commitments:** stock on hand, allocations, backorders.
- **Pipeline supply:** open purchase orders only.
- **Future install demand:** install forecast-based adjustment.

## Part-Level Forecasting Approach
Forecast outputs are part-level because procurement and stocking decisions are executed by part number. Model-level signals support adjustment and explainability but do not replace part-level decisioning.

## Model-Level Supporting Data
Model mappings, machine population, and install forecast provide contextual modifiers (usage-per-machine and install impact) while preserving part-level control outputs.

## Why Dealer Demand Is Part-Level Only
Dealer orders arrive as part orders and often lack reliable model attribution; forcing model allocation would add undocumented assumptions and reduce traceability.

## Why Open Purchase Orders Are Supply, Not Demand
Open purchase orders represent committed inbound inventory. Treating them as demand would double-count needs and distort projected stock and reorder recommendations.


### Decision layer output
Final inventory decisions are generated at `part_number` grain. Trace fields in `forecast_output.csv` include `stock_on_hand_qty`, `allocated_qty`, `backorder_qty`, `effective_stock_qty`, and `pipeline_supply_qty` to keep projected-stock and reorder calculations explainable.
