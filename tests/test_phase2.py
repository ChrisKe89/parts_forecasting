import json

import pandas as pd

from src.backtesting import run_backtest
from src.data.synthetic_generator import generate_synthetic_data
from src.forecasting.engine import run_forecast
from src.utils.config import ForecastingConfig


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


def test_forecast_combines_prd_demand_signals_and_inventory_position():
    weeks = pd.date_range("2026-01-05", periods=6, freq="W-MON")
    data = {
        "parts": pd.DataFrame(
            [
                {
                    "part_number": "P1",
                    "part_name": "Filter",
                    "model": "M1",
                    "smoothing_group": "B",
                    "minimum_order_quantity": 5,
                    "lead_time_days": 14,
                }
            ]
        ),
        "usage": pd.DataFrame(
            {
                "part_number": ["P1"] * 6,
                "model": ["M1"] * 6,
                "usage_date": weeks,
                "usage_qty": [10] * 6,
                "active_machines": [5] * 6,
            }
        ),
        "orders": pd.DataFrame(
            {
                "part_number": ["P1"] * 12,
                "order_date": list(weeks) * 2,
                "order_qty": [1] * 6 + [100] * 6,
                "fulfilled_qty": [1] * 12,
                "order_source": ["dealer"] * 6 + ["direct"] * 6,
                "order_status": ["fulfilled"] * 12,
            }
        ),
        "installs": pd.DataFrame(
            [
                {
                    "part_number": "P1",
                    "model": "M1",
                    "install_date": pd.Timestamp("2026-01-26"),
                    "install_qty": 3,
                    "install_status": "scheduled",
                    "projected_install_confidence": 1.0,
                },
                {
                    "part_number": "P1",
                    "model": "M1",
                    "install_date": pd.Timestamp("2026-01-26"),
                    "install_qty": 4,
                    "install_status": "projected",
                    "projected_install_confidence": 0.5,
                },
                {
                    "part_number": "P1",
                    "model": "M1",
                    "install_date": pd.Timestamp("2026-01-26"),
                    "install_qty": 99,
                    "install_status": "cancelled",
                    "projected_install_confidence": 1.0,
                },
            ]
        ),
        "stock": pd.DataFrame(
            [
                {
                    "part_number": "P1",
                    "snapshot_date": pd.Timestamp("2026-01-19"),
                    "stock_on_hand_qty": 100,
                    "allocated_qty": 3,
                    "unfulfilled_qty": 4,
                    "open_purchase_order_qty": 8,
                    "expected_arrival_date": pd.Timestamp("2026-01-26"),
                },
                {
                    "part_number": "P1",
                    "snapshot_date": pd.Timestamp("2026-01-19"),
                    "stock_on_hand_qty": 100,
                    "allocated_qty": 3,
                    "unfulfilled_qty": 4,
                    "open_purchase_order_qty": 99,
                    "expected_arrival_date": pd.Timestamp("2026-03-01"),
                },
            ]
        ),
    }

    forecast = run_forecast(
        data,
        as_of_date=pd.Timestamp("2026-01-19"),
        config=ForecastingConfig(smoothing_groups={"B": 0.5}, service_level_target=0.90),
    )

    row = forecast.iloc[0]
    assert row["base_forecast_demand"] == 10.0
    assert row["dealer_demand"] == 1.0
    assert row["usage_per_machine"] == 2.0
    assert row["install_adjustment"] == 10.0
    assert row["forecast_demand"] == 21.0
    assert row["effective_stock"] == 93.0
    assert row["pipeline_supply"] == 8.0
    assert row["projected_stock"] == 59.0
    assert row["final_order_qty"] == 0.0
    assert row["demand_source"] == "usage_dealer_install"


def test_forecast_uses_holt_only_when_history_and_trend_gate_pass():
    weeks = pd.date_range("2026-01-05", periods=6, freq="W-MON")
    base_data = {
        "parts": pd.DataFrame(
            [
                {
                    "part_number": "P1",
                    "part_name": "Filter",
                    "model": "M1",
                    "smoothing_group": "A",
                    "minimum_order_quantity": 0,
                    "lead_time_days": 7,
                }
            ]
        ),
        "usage": pd.DataFrame(
            {
                "part_number": ["P1"] * 6,
                "model": ["M1"] * 6,
                "usage_date": weeks,
                "usage_qty": [10, 12, 14, 16, 18, 20],
                "active_machines": [10] * 6,
            }
        ),
        "stock": pd.DataFrame(
            [
                {
                    "part_number": "P1",
                    "snapshot_date": pd.Timestamp("2026-02-09"),
                    "stock_on_hand_qty": 0,
                    "allocated_qty": 0,
                    "unfulfilled_qty": 0,
                    "open_purchase_order_qty": 0,
                    "expected_arrival_date": pd.Timestamp("2026-02-09"),
                }
            ]
        ),
    }
    config = ForecastingConfig(
        smoothing_groups={"A": 0.5},
        beta=0.5,
        minimum_history_points_for_holt=6,
        trend_significance_threshold=0.05,
    )

    trended = run_forecast(base_data, config=config).iloc[0]
    short_history = run_forecast({**base_data, "usage": base_data["usage"].head(5)}, config=config).iloc[0]

    assert trended["forecast_method"] == "holt"
    assert trended["forecast_trend"] > 0
    assert short_history["forecast_method"] == "exponential_smoothing"


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
