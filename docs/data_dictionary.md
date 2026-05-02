# Data Dictionary

Core columns: `part_id`, `part_name`, `model`, `usage_date`, `usage_qty`, `active_machines`, `install_date`, `install_qty`, `install_status`, `projected_install_confidence`, `stock_on_hand`, `stock_on_order`, `expected_arrival_date`, `lead_time_days`, `minimum_order_quantity`, `smoothing_group`.

Forecast output includes: part/model IDs, forecast method, base/trend/install-adjusted demand, outlier stats, safety stock, lead-time demand, reorder point, stock fields, trigger, recommended order, risk, service level, confidence score.

## Test Data Schema (data/test_data)
- parts.csv: part_id, part_name, model, smoothing_group, minimum_order_quantity, lead_time_days
- usage.csv: part_id, model, usage_date, usage_qty, active_machines
- installs.csv: part_id, model, install_date, install_qty, install_status, projected_install_confidence
- stock.csv: part_id, model, snapshot_date, stock_on_hand, stock_on_order, expected_arrival_date
