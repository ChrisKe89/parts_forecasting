# Implementation Notes

- Forecasting and inventory outputs are contract-driven by `docs/parts-forecasting-prd.md` and `docs/data-schema.md`.
- Input CSV validation behavior is defined in `docs/data-validation.md`.
- Runtime forecasting/backtesting paths are aligned with the documented production contract, while preserving compatibility with synthetic test fixtures used by the unit tests.


## Runtime workflow
Normal runtime uses `python -m src.main` against real raw CSV files in `data/raw`. Synthetic generation remains available only via explicit utility invocation (`python -m src.data.synthetic_generator`).

## Current runtime output audit (as of 2026-05-03)
Observed from `python -m src.main` against repository sample data:
- `forecast_output.csv` currently emits `forecast_demand` and stock/order fields (`stock_on_hand`, `stock_on_order`) rather than the full PRD/output-reference decision schema fields.
- `backtest_output.csv` currently contains run-level summary metrics (single row for sample data) rather than part-period error detail rows.
- Validation outputs are being generated and are structurally consistent with current loader behavior.

These are implementation/runtime observations only; PRD requirements in `docs/parts-forecasting-prd.md` remain the source of truth for target behavior.
