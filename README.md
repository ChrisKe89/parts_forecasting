# parts_forecasting

Deterministic, lead-time-aware spare parts forecasting prototype.

## Structure

- `data/raw`: input CSV files
- `data/processed`: optional intermediate outputs
- `data/output`: backtest outputs
- `src`: forecasting pipeline modules

## Input files (`data/raw`)

- `usage_data.csv`: `part_number,model,date,qty`
- `install_data.csv`: `model,date,qty`
- `emergency_orders.csv`: `part_number,date,qty`
- `cannibalised_parts.csv`: `part_number,date,qty`
- `part_model_mapping.csv`: `part_number,model`
- `stock_snapshot.csv` (optional): `part_number,stock_on_hand,stock_on_order,snapshot_date`

## Run

```bash
python -m src.main
```

## Outputs

- `data/output/forecast_backtest_results.csv`
- `data/output/forecast_backtest_summary.csv`
