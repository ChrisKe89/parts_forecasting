from __future__ import annotations

from pathlib import Path
import warnings
import pandas as pd

from data.schema import REQUIRED_COLUMNS


LEGACY_ALIASES = {
    "part_id": "part_number",
}


def _apply_legacy_aliases(df: pd.DataFrame, key: str) -> pd.DataFrame:
    for legacy, canonical in LEGACY_ALIASES.items():
        if legacy in df.columns and canonical not in df.columns:
            warnings.warn(
                f"Legacy column '{legacy}' found in {key}; please use '{canonical}'",
                UserWarning,
            )
            df = df.rename(columns={legacy: canonical})
    return df


def _validate(df: pd.DataFrame, key: str) -> pd.DataFrame:
    df = _apply_legacy_aliases(df, key)
    missing = [c for c in REQUIRED_COLUMNS[key] if c not in df.columns]
    if missing:
        raise ValueError(f"Missing {key} columns: {missing}")
    return df


def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def load_inputs(base_dir: Path) -> dict[str, pd.DataFrame]:
    data = {
        "parts": _validate(load_csv(base_dir / "parts.csv"), "parts"),
        "usage": _validate(load_csv(base_dir / "usage.csv"), "usage"),
        "installs": _validate(load_csv(base_dir / "installs.csv"), "installs"),
        "stock": _validate(load_csv(base_dir / "stock.csv"), "stock"),
    }
    for col in ["usage_date"]:
        data["usage"][col] = pd.to_datetime(data["usage"][col])
    data["installs"]["install_date"] = pd.to_datetime(data["installs"]["install_date"])
    data["stock"]["snapshot_date"] = pd.to_datetime(data["stock"]["snapshot_date"])
    data["stock"]["expected_arrival_date"] = pd.to_datetime(data["stock"]["expected_arrival_date"])
    return data
