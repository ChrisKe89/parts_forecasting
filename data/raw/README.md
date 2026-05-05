# Synthetic Parts Forecasting Dataset — 60% Service Level

This dataset is intentionally small and deterministic so it is easy to validate your repo output.

## Intended service level

Use dealer orders only, excluding cancelled orders.

Line service level:

```text
fully fulfilled dealer order lines / dealer order lines = 6 / 10 = 60%
```

Unit fill rate:

```text
fulfilled dealer quantity / dealer ordered quantity = 60 / 100 = 60%
```

These are deliberately the same because every dealer order line has `order_qty = 10`.

## Orders design

`orders.csv` contains exactly 10 dealer order lines:

- Orders `O-60-001` to `O-60-006` are fully fulfilled.
- Orders `O-60-007` to `O-60-010` are backorders with zero fulfilled quantity.

Therefore:

- Total dealer order lines = 10
- Fully fulfilled lines = 6
- Total dealer demand units = 100
- Fulfilled dealer units = 60
- Backorder units = 40

## Files included

Required schema files:

- `parts_master.csv`
- `part_model_mapping.csv`
- `internal_parts_usage.csv`
- `orders.csv`
- `stock_snapshot.csv`
- `open_purchase_orders.csv`
- `active_machine_population.csv`

Optional/supporting files:

- `install_forecast.csv`
- `expected_metrics.csv`

## Notes

This is a validation dataset, not a realistic production-scale dataset. It is designed to make service-level calculation obvious before testing forecast improvement logic.
