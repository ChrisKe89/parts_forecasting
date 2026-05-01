from __future__ import annotations

import pandas as pd


def build_installed_base(installs_monthly: pd.DataFrame) -> pd.DataFrame:
    if installs_monthly.empty:
        return installs_monthly
    installed_base = installs_monthly.sort_values(["model", "month"]).copy()
    installed_base["installed_base"] = installed_base.groupby("model")["qty"].cumsum()
    return installed_base
