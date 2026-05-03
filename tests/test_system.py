import pandas as pd
from pathlib import Path

from src.forecasting.calculations import safety_stock, service_level_to_z
from src.inventory.logic import demand_during_lead_time, reorder_point, apply_moq, rolling_ordering_simulation
from src.data.synthetic_generator import generate_synthetic_data
from src.data.loader import load_inputs
from src.forecasting.engine import run_forecast


def test_lead_time_demand_calculation():
    assert demand_during_lead_time(10, 90, period_days=7) == 10 * (90 / 7)


def test_safety_stock_calculation():
    z = service_level_to_z(0.9)
    ss = safety_stock(5, 12, z)
    assert ss > 0


def test_reorder_point_calculation():
    assert reorder_point(100, 12) == 112


def test_moq_behavior_and_no_negative_orders():
    order_qty, moq_applied = apply_moq(3, 10, reorder_triggered=True)
    assert order_qty == 10 and moq_applied
    order_qty2, _ = apply_moq(-5, 10, reorder_triggered=True)
    assert order_qty2 == 0


def test_no_order_when_above_rop():
    order_qty, _ = apply_moq(5, 10, reorder_triggered=False)
    assert order_qty == 0


def test_order_triggered_when_below_rop():
    assert 5 < reorder_point(4, 2)


def test_weekly_rolling_order_arrival_logic():
    incoming = pd.DataFrame({"stock_on_order": [20], "expected_arrival_date": [pd.Timestamp("2026-03-15")]})
    sim = rolling_ordering_simulation(10, 2, 90, incoming, pd.Timestamp("2026-01-01"))
    assert sim["arrival_date"] == pd.Timestamp("2026-04-01")


def test_install_adjustment_available_unavailable(tmp_path: Path):
    data = {
        "parts": pd.DataFrame([{"part_number":"P1","part_name":"x","model":"M1","smoothing_group":"A","minimum_order_quantity":1,"lead_time_days":30}]),
        "usage": pd.DataFrame([{"part_number":"P1","model":"M1","usage_date":pd.Timestamp("2026-01-01"),"usage_qty":2,"active_machines":10}]),
        "installs": pd.DataFrame([{"part_number":"P1","model":"M1","install_date":pd.Timestamp("2026-02-01"),"install_qty":1,"install_status":"scheduled","projected_install_confidence":1.0}]),
        "stock": pd.DataFrame([{"part_number":"P1","snapshot_date":pd.Timestamp("2026-01-01"),"stock_on_hand_qty":5,"allocated_qty":0,"unfulfilled_qty":0,"open_purchase_order_qty":0,"expected_arrival_date":pd.Timestamp("2026-02-01")}]),
    }
    out = run_forecast(data)
    assert out["install_adjustment_available"].any()

    data["installs"] = data["installs"].iloc[0:0]
    out2 = run_forecast(data)
    assert (~out2["install_adjustment_available"]).all()


def test_sparse_history_fallback():
    data = {
        "parts": pd.DataFrame([{"part_number": "P1", "model": "M1", "smoothing_group": "C", "minimum_order_quantity": 5, "lead_time_days": 90}]),
        "usage": pd.DataFrame([
            {"part_number": "P1", "model": "M1", "usage_date": pd.Timestamp("2026-01-01"), "usage_qty": 2, "active_machines": 10},
            {"part_number": "P1", "model": "M1", "usage_date": pd.Timestamp("2026-02-01"), "usage_qty": 3, "active_machines": 10},
        ]),
        "installs": pd.DataFrame(columns=["part_number", "model", "install_date", "install_qty", "install_status", "projected_install_confidence"]),
        "stock": pd.DataFrame([{"part_number": "P1", "snapshot_date": pd.Timestamp("2026-02-01"), "stock_on_hand_qty": 1, "allocated_qty": 0, "unfulfilled_qty": 0, "open_purchase_order_qty": 0, "expected_arrival_date": pd.Timestamp("2026-03-01")}]),
    }
    out = run_forecast(data)
    assert out.iloc[0]["sparse_history_fallback_applied"]

def test_part_level_aggregation_and_trace_fields():
    data = {
        "parts": pd.DataFrame([
            {"part_number": "P1", "part_name": "x", "model": "M1", "smoothing_group": "A", "minimum_order_quantity": 12, "lead_time_days": 30},
            {"part_number": "P1", "part_name": "x", "model": "M2", "smoothing_group": "A", "minimum_order_quantity": 12, "lead_time_days": 30},
        ]),
        "usage": pd.DataFrame([
            {"part_number": "P1", "model": "M1", "usage_date": pd.Timestamp("2026-01-01"), "usage_qty": 5, "active_machines": 10},
            {"part_number": "P1", "model": "M2", "usage_date": pd.Timestamp("2026-01-01"), "usage_qty": 7, "active_machines": 14},
        ]),
        "installs": pd.DataFrame([
            {"part_number": "P1", "model": "M1", "install_date": pd.Timestamp("2026-02-01"), "install_qty": 3, "install_status": "scheduled", "projected_install_confidence": 1.0},
            {"part_number": "P1", "model": "M2", "install_date": pd.Timestamp("2026-02-01"), "install_qty": 2, "install_status": "projected", "projected_install_confidence": 0.5},
        ]),
        "stock": pd.DataFrame([
            {"part_number": "P1", "snapshot_date": pd.Timestamp("2026-01-01"), "stock_on_hand_qty": 20, "allocated_qty": 2, "unfulfilled_qty": 3, "open_purchase_order_qty": 10, "expected_arrival_date": pd.Timestamp("2026-01-20")},
        ]),
    }
    out = run_forecast(data, as_of_date=pd.Timestamp("2026-01-01"))
    assert len(out) == 1
    row = out.iloc[0]
    assert row["stock_on_hand_qty"] == 20
    assert row["allocated_qty"] == 2
    assert row["backorder_qty"] == 3
    assert row["effective_stock_qty"] == 15
    assert row["pipeline_supply_qty"] == 10
    assert row["install_adjustment_available"]
    assert isinstance(row["recommendation_explanation"], str) and row["recommendation_explanation"]
