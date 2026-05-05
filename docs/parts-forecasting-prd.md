# Parts Forecasting & Inventory Recommendation System PRD

## Purpose and Business Objective

This system provides deterministic, explainable spare-parts demand forecasting and inventory reorder recommendations. The objective is to reduce stockout risk and excess inventory by combining historical demand, current stock commitments, and inbound supply in a traceable workflow.

## Core Principles

- Deterministic outputs for the same inputs and configuration.
- Explainable intermediate calculations at part level.
- Strict schema-driven data contracts.
- Separation of demand signals from supply signals.
- No black-box forecasting methods.

## Demand Sources

1. **Internal parts usage (`internal_parts_usage.csv`)** as the primary demand signal.
1. **Dealer orders (`orders.csv`, `order_source=dealer`)** as part-level external demand.
1. **Install forecast (`install_forecast.csv`)** as model-driven demand adjustment:
   - scheduled installs counted at 100%
   - projected installs weighted by confidence
   - cancelled installs ignored

## Supply Sources

- **Stock snapshot (`stock_snapshot.csv`)** for stock-on-hand baseline.
- **Allocated stock (`stock_snapshot.csv`)** as committed inventory.
- **Backorders (`orders.csv`)** from unfulfilled dealer demand.
- **Open purchase orders (`open_purchase_orders.csv`)** as pipeline supply.

## Forecasting Flow

1. Validate required and optional input files against schema.
1. Prepare internal usage history and part-model compatibility.
1. Detect outliers using Z-score threshold and preserve original values for traceability.
1. Compute usage-per-machine from usage and active machine population.
1. Build base demand forecast (exponential smoothing by default; Holt trend only when history and significance requirements are met).
1. Add dealer demand contribution at part level.
1. Apply install demand adjustment.
1. Produce final demand used by inventory logic.

## Inventory Logic

- `effective_stock = stock_on_hand_qty - allocated_qty - backorder_qty`
- `pipeline_supply = sum(open_purchase_order_qty arriving before target date)`
- `lead_time_demand` is demand expected during replenishment lead time.
- `projected_stock = effective_stock + pipeline_supply - lead_time_demand`

## Reorder Logic

- `reorder_point = lead_time_demand + safety_stock`
- If `projected_stock < reorder_point`, trigger reorder.
- If not, recommended order quantity is zero.

## MOQ Logic

- MOQ is applied **after** raw required order quantity is calculated.
- MOQ does not influence whether reorder is triggered.

## Backtesting Expectations

Backtesting must support configurable train/test windows and produce:

- MAE
- RMSE
- Forecast bias
- Under/over forecast counts
- Service-level estimate
- Stockout count

## Validation Expectations

- Schema and contract validation must run before forecasting.
- Errors stop execution.
- Warnings are reported while processing continues.
- Validation issues are written to `schema_validation_report.csv`.

## Output Expectations

The run must generate documented output artifacts including:

- forecast output
- backtest output
- validation reports and summaries

See `docs/output-reference.md` for output-level definitions.

## Known Limitations

- Dealer demand is modeled at part level only; no dealer-demand model allocation is inferred.
- Forecast quality remains dependent on completeness and correctness of usage history and mappings.
- Documentation contract may be ahead of some runtime loader details until follow-up implementation alignment tasks are completed.
