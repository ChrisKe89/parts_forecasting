# Data Validation Behavior

## Global CSV Rules
- UTF-8 CSV with header row.
- Header names must exactly match `docs/data-schema.md`.
- No duplicate columns.
- Date columns must parse as dates.
- Numeric columns must parse as numeric without silent coercion.

## Severity Model
- **Errors:** stop forecasting execution.
- **Warnings:** captured in report; processing continues.

## Column-Level Validation Coverage (current implementation)

| File | Column | Validation |
|---|---|---|
| parts_master.csv | minimum_order_qty | numeric and `>= 0` |
| parts_master.csv | default_lead_time_days | numeric and `>= 0` |
| part_model_mapping.csv | part_number, model | required non-missing columns |
| internal_parts_usage.csv | usage_date | valid date |
| internal_parts_usage.csv | usage_qty | numeric and `>= 0` |
| orders.csv | order_date, order_fulfilment_date | valid dates |
| orders.csv | order_qty, fulfilled_qty | numeric and `>= 0`; `fulfilled_qty <= order_qty` |
| orders.csv | order_source | enum: dealer/direct/internal/other |
| orders.csv | order_status | enum: fulfilled/partially_fulfilled/backorder/cancelled |
| stock_snapshot.csv | stock_snapshot_date | valid date |
| stock_snapshot.csv | stock_on_hand_qty, allocated_qty | numeric and `>= 0` |
| open_purchase_orders.csv | purchase_order_date, expected_arrival_date | valid dates |
| open_purchase_orders.csv | purchase_order_qty, received_qty, open_purchase_order_qty | numeric and `>= 0`; arithmetic check `open = purchase - received` |
| open_purchase_orders.csv | purchase_order_status | enum: open/partially_received/received/cancelled |
| active_machine_population.csv | population_snapshot_date | valid date |
| active_machine_population.csv | active_machine_qty | numeric and `>= 0` |
| active_machine_population.csv | owner_group | enum: direct/customer/dealer |
| active_machine_population.csv | service_group | enum: direct/dealer |
| install_forecast.csv (if present) | install_date | valid date |
| install_forecast.csv (if present) | install_qty | numeric and `>= 0` |
| install_forecast.csv (if present) | install_status | enum: scheduled/projected/cancelled |
| install_forecast.csv (if present) | projected_install_confidence | numeric in `[0,1]` |

## Cross-Table Validation
- Unknown model when joining usage with active population is logged as a warning.

## Validation Output File
Validation issues are written to `schema_validation_report.csv` with columns:
`file_name,column_name,row_number,severity,message`.
