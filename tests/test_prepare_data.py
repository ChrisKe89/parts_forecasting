import pandas as pd

from src.prepare_data import clean_input_data, prepare_monthly_data


def test_prepare_monthly_handles_empty_optional_inputs_without_keyerror():
    data = {
        "usage": pd.DataFrame(
            {
                "part_number": ["p1"],
                "model": ["m1"],
                "date": ["2025-01-15"],
                "qty": [2],
            }
        ),
        "installs": pd.DataFrame({"model": ["m1"], "date": ["2025-01-01"], "qty": [10]}),
        "emergency": pd.DataFrame(columns=["part_number", "date", "qty"]),
        "cannibalised": pd.DataFrame(columns=["part_number", "date", "qty"]),
        "mapping": pd.DataFrame({"part_number": ["p1"], "model": ["m1"]}),
        "stock": pd.DataFrame(columns=["part_number", "stock_on_hand", "stock_on_order", "snapshot_date"]),
    }

    cleaned = clean_input_data(data)
    monthly = prepare_monthly_data(cleaned)

    assert list(monthly["usage"].columns) == ["part_number", "model", "month", "qty"]
    assert list(monthly["emergency"].columns) == ["part_number", "model", "month", "qty"]
    assert list(monthly["cannibalised"].columns) == ["part_number", "model", "month", "qty"]
    assert monthly["emergency"].empty
    assert monthly["cannibalised"].empty


def test_clean_input_data_standardizes_casing_types_and_drops_null_keys():
    data = {
        "usage": pd.DataFrame(
            {
                "part_number": [" p1 ", None],
                "model": [" m1 ", "m2"],
                "date": ["2025-01-15", "bad-date"],
                "qty": ["3", "bad"],
            }
        ),
        "installs": pd.DataFrame({"model": ["m1"], "date": ["2025-01-01"], "qty": ["5"]}),
        "emergency": pd.DataFrame(columns=["part_number", "date", "qty"]),
        "cannibalised": pd.DataFrame(columns=["part_number", "date", "qty"]),
        "mapping": pd.DataFrame({"part_number": ["p1"], "model": ["m1"]}),
        "stock": pd.DataFrame(
            {
                "part_number": ["p1"],
                "stock_on_hand": ["4"],
                "stock_on_order": ["1"],
                "snapshot_date": ["2025-01-31"],
            }
        ),
    }

    cleaned = clean_input_data(data)
    usage = cleaned["usage"]

    assert len(usage) == 1
    assert usage.iloc[0]["part_number"] == "P1"
    assert usage.iloc[0]["model"] == "M1"
    assert pd.api.types.is_datetime64_any_dtype(usage["date"])
    assert usage.iloc[0]["qty"] == 3
