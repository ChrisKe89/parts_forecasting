"""Data loading utilities for CSV inputs."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import pandas as pd


REQUIRED_COLUMNS = {
    "usage": ["part_number", "model", "date", "qty"],
    "installs": ["model", "date", "qty"],
    "emergency": ["part_number", "date", "qty"],
    "cannibalised": ["part_number", "date", "qty"],
    "mapping": ["part_number", "model"],
    "stock": ["part_number", "stock_on_hand", "stock_on_order", "snapshot_date"],
}


def _read_csv_if_exists(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def load_input_data(input_files: Dict[str, Path]) -> Dict[str, pd.DataFrame]:
    data = {name: _read_csv_if_exists(path) for name, path in input_files.items()}

    for name, required in REQUIRED_COLUMNS.items():
        if data[name].empty:
            continue
        missing = set(required) - set(data[name].columns)
        if missing:
            raise ValueError(f"{name} is missing required columns: {sorted(missing)}")

    return data
