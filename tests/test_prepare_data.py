import pandas as pd

from src.data.loader import load_inputs


def test_load_inputs_missing_required_files_fails(tmp_path):
    _, issues, valid = load_inputs(tmp_path)
    assert not valid
    assert (issues["severity"] == "error").any()
