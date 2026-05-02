# Parts Forecasting System

Deterministic, explainable spare-parts demand forecasting and inventory reorder recommendation.

## What the system does
- Validates schema-defined CSV inputs.
- Forecasts part-level demand using internal usage, dealer demand, and install adjustments.
- Computes stock position, reorder point, and MOQ-constrained order recommendations.
- Produces forecast, backtest, and validation outputs.

## Input file location
Place input CSVs in your configured raw data directory (commonly `data/raw/`) using the exact filenames and headers documented in `docs/data-schema.md`.

## Required input files
- `parts_master.csv`
- `part_model_mapping.csv`
- `internal_parts_usage.csv`
- `orders.csv`
- `stock_snapshot.csv`
- `open_purchase_orders.csv`
- `active_machine_population.csv`

## Optional input file
- `install_forecast.csv`

## How to run
```bash
python -m src.main
```

## Expected outputs
See `docs/output-reference.md` for output definitions:
- `forecast_output.csv`
- `backtest_output.csv`
- `validation_report.csv`
- `validation_summary.csv`
- `schema_validation_report.csv`

## Run tests
```bash
pytest -q
```

## Notes on test/synthetic data
Synthetic and test data are for development/testing support only and are not part of normal production workflow.


Runtime note: `python -m src.main` reads real CSVs from `data/raw` by default and never generates synthetic data. Use `python -m src.data.synthetic_generator` for synthetic test data only. Backtest runs in default `--mode all` when enough history exists; otherwise forecast still completes and backtest is skipped with a message.
