import pandas as pd
import pytest

from data.loader import load_inputs


def test_load_inputs_validates_required_columns(tmp_path):
    pd.DataFrame([{"part_number":"P1","part_name":"a","model":"M1","smoothing_group":"A","minimum_order_quantity":1,"lead_time_days":90}]).to_csv(tmp_path/"parts.csv", index=False)
    pd.DataFrame([{"part_number":"P1","model":"M1","usage_date":"2026-01-01","usage_qty":1,"active_machines":10}]).to_csv(tmp_path/"usage.csv", index=False)
    pd.DataFrame([{"part_number":"P1","model":"M1","install_date":"2026-01-10","install_qty":1,"install_status":"scheduled","projected_install_confidence":1.0}]).to_csv(tmp_path/"installs.csv", index=False)
    pd.DataFrame([{"part_number":"P1","model":"M1","snapshot_date":"2026-01-01","stock_on_hand":5,"stock_on_order":0,"expected_arrival_date":"2026-02-01"}]).to_csv(tmp_path/"stock.csv", index=False)
    loaded = load_inputs(tmp_path)
    assert pd.api.types.is_datetime64_any_dtype(loaded["usage"]["usage_date"])


def test_load_inputs_missing_column_raises(tmp_path):
    pd.DataFrame([{"part_number":"P1"}]).to_csv(tmp_path/"parts.csv", index=False)
    pd.DataFrame(columns=["part_number","model","usage_date","usage_qty","active_machines"]).to_csv(tmp_path/"usage.csv", index=False)
    pd.DataFrame(columns=["part_number","model","install_date","install_qty","install_status","projected_install_confidence"]).to_csv(tmp_path/"installs.csv", index=False)
    pd.DataFrame(columns=["part_number","model","snapshot_date","stock_on_hand","stock_on_order","expected_arrival_date"]).to_csv(tmp_path/"stock.csv", index=False)
    with pytest.raises(ValueError):
        load_inputs(tmp_path)
