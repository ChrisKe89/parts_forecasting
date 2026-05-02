# Data Validation Behavior

## Global CSV Rules
- UTF-8 CSV with header row.
- Header names must exactly match `docs/data-schema.md`.
- No duplicate columns.
- Date columns must parse as dates.
- Numeric columns must parse as numeric without silent coercion.

## Required vs Optional Files
- Required files must exist and pass schema checks.
- Optional file (`install_forecast.csv`) may be absent.
- If optional file is present, schema validation still applies.

## Severity Model
- **Errors:** stop forecasting execution.
- **Warnings:** captured in report; processing continues.

## Schema Errors vs Warnings
### Errors (stop)
- Missing required file
- Missing required column
- Invalid data type for required processing
- Invalid enum value where constrained
- Negative quantities unless explicitly allowed
- Invalid relationships that break core joins

### Warnings (continue)
- Unknown models in optional/supporting joins
- Missing optional columns
- Outliers flagged by z-score policy
- Partial inconsistencies that do not block core calculations

## Cross-Table Validation
- `part_number` in mapping/usage/orders/stock/PO must exist in `parts_master.csv`.
- `part_number` + `model` usage combinations should exist in `part_model_mapping.csv` (warn if unknown).
- Open PO quantities must satisfy arithmetic consistency.

## Date Rules
- Must use valid calendar dates.
- Forecasting comparisons rely on consistent chronology.
- Future/past dates are allowed where contextually valid (history vs projected records).

## Numeric Rules
- Quantity fields are non-negative.
- `fulfilled_qty <= order_qty`.
- `open_purchase_order_qty = purchase_order_qty - received_qty`.
- Confidence values are bounded in `[0,1]`.

## Allowed Enum Values
- `order_source`: dealer, direct, internal, other
- `order_status`: fulfilled, partially_fulfilled, backorder, cancelled
- `purchase_order_status`: open, partially_received, received, cancelled
- `owner_group`: direct, customer, dealer
- `service_group`: direct, dealer
- `install_status`: scheduled, projected, cancelled

## Validation Output File
Validation issues are written to:

`schema_validation_report.csv`

Required columns:
`file_name,column_name,row_number,severity,message`

Rules:
- Errors stop forecasting.
- Warnings are written to the report and processing continues.


## Runtime workflow alignment
- Normal runtime path validates real CSVs in `data/raw` and does not call synthetic data generation.
- Missing required files fail with clear errors (including file path).
- Missing optional `install_forecast.csv` is allowed; processing continues.
