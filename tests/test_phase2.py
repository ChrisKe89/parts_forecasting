import json

from src.backtesting import run_backtest
from src.data.synthetic_generator import generate_synthetic_data
from src.forecasting.engine import run_forecast


def test_synthetic_scale_and_baseline(tmp_path):
    data = generate_synthetic_data(tmp_path)
    assert data["parts"]["part_id"].nunique() == 1000
    assert data["machine_models"]["model_id"].nunique() == 50
    assert data["usage"]["week_start_date"].nunique() == 104
    assert 0.55 <= data["baseline_service_level"] <= 0.65


def test_backtest_outputs_and_supplier_lifecycle(tmp_path):
    data = generate_synthetic_data(tmp_path)
    summary, weekly, concerns = run_backtest(data, output_dir=tmp_path)
    assert "baseline_service_level" in summary.columns
    assert "model_service_level" in summary.columns
    assert "service_level_improvement" in summary.columns
    assert (weekly["demand_source"] == "usage_only").all()
    supplier = (tmp_path / "supplier_order_simulation.csv").read_text()
    assert "partial" in supplier
    assert "delayed" in supplier
    assert "cancelled" in supplier
    concerns_json = json.loads((tmp_path / "concerns_report.json").read_text())
    assert "concerns" in concerns_json


def test_live_forecast_fields_and_moq(tmp_path):
    data = generate_synthetic_data(tmp_path)
    f = run_forecast(data)
    required = {
        "part_id", "forecast_demand", "lead_time_demand", "safety_stock", "reorder_point", "stock_on_hand",
        "stock_on_order", "raw_recommended_qty", "final_order_qty", "minimum_order_qty", "order_multiple_qty",
        "moq_applied", "order_multiple_applied", "risk_level", "explanation", "demand_source",
    }
    assert required.issubset(set(f.columns))


from src.data.loader import load_inputs


def test_validation_rejects_invalid_enums_and_arithmetic(tmp_path):
    import pandas as pd
    d=tmp_path
    pd.DataFrame([{"part_number":"P1","part_description":"x","smoothing_group":"A","minimum_order_qty":1,"default_lead_time_days":7,"is_active":True}]).to_csv(d/"parts_master.csv",index=False)
    pd.DataFrame([{"part_number":"P1","model":"M1"}]).to_csv(d/"part_model_mapping.csv",index=False)
    pd.DataFrame([{"part_number":"P1","model":"M1","usage_date":"2026-01-01","usage_qty":1}]).to_csv(d/"internal_parts_usage.csv",index=False)
    pd.DataFrame([{"order_no":"O1","part_number":"P1","order_qty":1,"fulfilled_qty":2,"order_date":"2026-01-01","order_source":"bad","order_status":"bad","order_fulfilment_date":"2026-01-01"}]).to_csv(d/"orders.csv",index=False)
    pd.DataFrame([{"part_number":"P1","stock_snapshot_date":"2026-01-01","stock_on_hand_qty":1,"allocated_qty":0}]).to_csv(d/"stock_snapshot.csv",index=False)
    pd.DataFrame([{"purchase_order_no":"PO1","part_number":"P1","purchase_order_qty":5,"received_qty":1,"open_purchase_order_qty":99,"purchase_order_date":"2026-01-01","purchase_order_status":"wrong","expected_arrival_date":"2026-01-08"}]).to_csv(d/"open_purchase_orders.csv",index=False)
    pd.DataFrame([{"model":"M1","population_snapshot_date":"2026-01-01","active_machine_qty":10,"owner_group":"bad","service_group":"bad"}]).to_csv(d/"active_machine_population.csv",index=False)
    pd.DataFrame([{"model":"M1","part_number":"P1","install_date":"2026-01-01","install_qty":1,"install_status":"wrong","projected_install_confidence":1.5}]).to_csv(d/"install_forecast.csv",index=False)

    _, issues, valid = load_inputs(d)
    assert not valid
    msgs = "\n".join(issues["message"].tolist())
    assert "Invalid enum" in msgs
    assert "fulfilled_qty cannot exceed order_qty" in msgs
    assert "open_purchase_order_qty must equal purchase_order_qty - received_qty" in msgs
    assert "Confidence out of bounds" in msgs
