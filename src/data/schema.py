from __future__ import annotations

REQUIRED_COLUMNS = {
    "parts": [
        "part_number", "part_name", "model", "smoothing_group", "minimum_order_quantity", "lead_time_days",
    ],
    "usage": ["part_number", "model", "usage_date", "usage_qty", "active_machines"],
    "installs": [
        "part_number", "model", "install_date", "install_qty", "install_status", "projected_install_confidence",
    ],
    "stock": [
        "part_number", "snapshot_date", "stock_on_hand_qty", "allocated_qty", "unfulfilled_qty", "open_purchase_order_qty", "expected_arrival_date",
    ],
}
