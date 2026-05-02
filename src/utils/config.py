from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ForecastingConfig:
    smoothing_groups: dict[str, float] = field(default_factory=lambda: {"A": 0.7, "B": 0.4, "C": 0.2})
    beta: float = 0.2
    z_threshold: float = 3.0
    service_level_target: float = 0.90
    lead_time_days_default: int = 90
    lead_time_buffer_days: int = 7
    minimum_history_points_for_holt: int = 6
    trend_significance_threshold: float = 0.05
    moq_default: int = 0
    random_seed: int = 42


DEFAULT_CONFIG = ForecastingConfig()
