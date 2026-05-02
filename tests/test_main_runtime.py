from __future__ import annotations

from pathlib import Path
import pandas as pd
import pytest

from main import main


def _write_base_inputs(base: Path, with_install: bool = True, short_history: bool = False) -> None:
    base.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([{"part_number":"P1","part_description":"Part 1","smoothing_group":"A","minimum_order_qty":5,"default_lead_time_days":30,"is_active":True}]).to_csv(base / "parts_master.csv", index=False)
    pd.DataFrame([{"part_number":"P1","model":"M1"}]).to_csv(base / "part_model_mapping.csv", index=False)
    usage_dates = ["2026-01-01", "2026-02-01", "2026-03-01", "2026-04-01", "2026-05-01", "2026-06-01"]
    if short_history:
        usage_dates = ["2026-05-01", "2026-06-01"]
    pd.DataFrame([{"part_number":"P1","model":"M1","usage_date":d,"usage_qty":2} for d in usage_dates]).to_csv(base / "internal_parts_usage.csv", index=False)
    pd.DataFrame([{"order_no":"O1","part_number":"P1","order_qty":10,"fulfilled_qty":8,"order_date":"2026-06-01","order_source":"dealer","order_status":"partially_fulfilled","order_fulfilment_date":"2026-06-15"}]).to_csv(base / "orders.csv", index=False)
    pd.DataFrame([{"part_number":"P1","stock_snapshot_date":"2026-06-01","stock_on_hand_qty":20,"allocated_qty":2}]).to_csv(base / "stock_snapshot.csv", index=False)
    pd.DataFrame([{"purchase_order_no":"PO1","part_number":"P1","purchase_order_qty":12,"received_qty":2,"open_purchase_order_qty":10,"purchase_order_date":"2026-06-10","purchase_order_status":"open","expected_arrival_date":"2026-06-20"}]).to_csv(base / "open_purchase_orders.csv", index=False)
    pd.DataFrame([{"model":"M1","population_snapshot_date":"2026-06-01","active_machine_qty":100,"owner_group":"customer","service_group":"dealer"}]).to_csv(base / "active_machine_population.csv", index=False)
    if with_install:
        pd.DataFrame([{"part_number":"P1","model":"M1","install_date":"2026-07-01","install_qty":3,"install_status":"scheduled","projected_install_confidence":1.0}]).to_csv(base / "install_forecast.csv", index=False)


def test_main_defaults_read_raw_and_write_output(tmp_path, monkeypatch):
    raw = tmp_path / "data" / "raw"
    out = tmp_path / "data" / "output"
    _write_base_inputs(raw)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["prog"])
    code = main()
    assert code == 0
    assert (out / "forecast_output.csv").exists()


def test_custom_input_output_dirs_and_skip_backtest(tmp_path, monkeypatch):
    raw = tmp_path / "in"
    out = tmp_path / "out"
    _write_base_inputs(raw)
    monkeypatch.setattr("sys.argv", ["prog", "--input-dir", str(raw), "--output-dir", str(out), "--skip-backtest"])
    code = main()
    assert code == 0
    assert (out / "forecast_output.csv").exists()
    assert not (out / "backtest_output.csv").exists()


def test_missing_required_file_fails_clearly(tmp_path, monkeypatch, capsys):
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["prog"])
    code = main()
    out = capsys.readouterr().out
    assert code == 1
    assert "Missing required input file" in out


def test_optional_install_missing_does_not_fail(tmp_path, monkeypatch):
    raw = tmp_path / "raw"
    out = tmp_path / "output"
    _write_base_inputs(raw, with_install=False)
    monkeypatch.setattr("sys.argv", ["prog", "--input-dir", str(raw), "--output-dir", str(out)])
    code = main()
    forecast = pd.read_csv(out / "forecast_output.csv")
    assert code == 0
    assert (forecast["part_number"] == "P1").all()


def test_insufficient_history_skips_backtest(tmp_path, monkeypatch, capsys):
    raw = tmp_path / "raw"
    out = tmp_path / "output"
    _write_base_inputs(raw, short_history=True)
    monkeypatch.setattr("sys.argv", ["prog", "--input-dir", str(raw), "--output-dir", str(out)])
    code = main()
    stdout = capsys.readouterr().out
    assert code == 0
    assert "insufficient usage history" in stdout
    assert (out / "forecast_output.csv").exists()
