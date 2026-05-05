# Backtesting (Proof Mode)

Proof mode answers: **Given the same demand, did the model improve service level versus baseline?**

## Windowing

- Train window: first 18 months of available history.
- Test window: final 6 months.
- Short-history fixtures that cannot fill the calendar window preserve the same 18:6 train/test ratio by dated observation count.
- Replay cadence: week-by-week over the test window.

## Demand and replay contract

- Replay demand source is `usage_qty` from usage history (`demand_source=usage_only`).
- Test-period demand is fixed during replay.
- Stock is carried forward each week (no reset).
- Backorders are carried forward each week.

## Supplier lifecycle simulation

Replay includes supplier order state transitions:

- `open`
- `partial`
- `full`
- `delayed`
- `cancelled`

Rules:

- Supplier orders are not instant receipts.
- Partial receipts add only `received_qty` to stock.
- Delayed orders keep `remaining_qty` in `stock_on_order`.
- Cancelled quantities never become stock and are tracked via `cancelled_qty`.

## Metrics produced

- Service-level comparison: baseline/model/improvement.
- Fill-rate comparison: baseline/model/improvement.
- Stockout comparison and reduction.
- Inventory trade-offs: average/peak/inventory change metrics.
- Order flow: baseline/model ordered qty, received qty, ending open/backorder quantities.
- Forecast diagnostics: MAE, RMSE, bias (where provided by run summary).

## Fail and concern behavior

- Synthetic baseline service-level target is 55%–65%.
- When `enforce_fail_conditions=True`, run fails if synthetic baseline is out of range.
- Structured `concerns_report.json` highlights risk categories (service level, inventory realism, etc.).

## Output files

- `backtest_summary.json`
- `backtest_weekly_detail.csv`
- `concerns_report.json`
- `supplier_order_simulation.csv`
- `inventory_position_simulation.csv`
- `model_recommendations.csv`
